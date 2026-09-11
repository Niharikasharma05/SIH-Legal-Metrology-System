import os
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from auth import (
    UserCreate,
    UserRead,
    UserUpdate,
    auth_backend,
    current_active_officer,
    fastapi_users,
)
from db import SessionLocal
from models import Scan, ScanImage, User
from settings import settings
from storage import ensure_bucket, image_object_key, upload_image


ALLOWED_LABELS = {"front", "back", "side", "other"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.is_local:
        ensure_bucket()
    yield


app = FastAPI(
    title="SetuCheck Legal Metrology Engine",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "environment": settings.app_env,
    }


@app.post("/api/scans", status_code=202)
async def create_scan(
    files: List[UploadFile] = File(...),
    labels: Optional[List[str]] = Form(None),
    product_name: Optional[str] = Form(None),
    user: User = Depends(current_active_officer),
):
    if len(files) > 4:
        raise HTTPException(
            status_code=422,
            detail="A scan must contain between 1 and 4 images",
        )

    if labels is not None and len(labels) != len(files):
        raise HTTPException(
            status_code=422,
            detail="The number of labels must match the number of files",
        )

    if labels is None:
        labels = ["other"] * len(files)

    if any(label not in ALLOWED_LABELS for label in labels):
        raise HTTPException(
            status_code=422,
            detail="Invalid image label",
        )

    session = SessionLocal()

    try:
        scan = Scan(
            input_type="image",
            status="pending",
            product_name=product_name,
            scanned_by_id=user.id,
        )

        session.add(scan)
        session.flush()

        for file, label in zip(files, labels):
            contents = await file.read()

            if not contents:
                raise HTTPException(
                    status_code=422,
                    detail="Uploaded image is empty",
                )

            image_id = uuid.uuid4()
            extension = (
                os.path.splitext(file.filename)[1]
                if file.filename
                else ".jpg"
            )

            object_key = image_object_key(
                scan.id,
                image_id,
                extension,
            )

            upload_image(
                object_key,
                contents,
                file.content_type or "image/jpeg",
            )

            image = ScanImage(
                id=image_id,
                scan_id=scan.id,
                object_key=object_key,
                status="pending",
                label=label,
            )

            session.add(image)

        session.commit()

        return {
            "id": str(scan.id),
            "status": "pending",
            "image_count": len(files),
        }

    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.get("/api/scans/{scan_id}")
def get_scan(
    scan_id: uuid.UUID,
    user: User = Depends(current_active_officer),
):
    session = SessionLocal()

    try:
        scan = session.execute(
            select(Scan)
            .where(Scan.id == scan_id)
        ).scalar_one_or_none()

        if scan is None:
            raise HTTPException(
                status_code=404,
                detail="Scan not found",
            )

        images = session.execute(
            select(ScanImage)
            .where(ScanImage.scan_id == scan.id)
            .order_by(ScanImage.created_at)
        ).scalars().all()

        return {
            "id": str(scan.id),
            "status": scan.status,
            "input_type": scan.input_type,
            "product_name": scan.product_name,
            "category": scan.category,
            "raw_text": scan.raw_text,
            "mrp": scan.mrp,
            "net_quantity": scan.net_quantity,
            "date_of_mfg": scan.date_of_mfg,
            "manufacturer_address": scan.manufacturer_address,
            "consumer_care": scan.consumer_care,
            "font_ok": scan.font_ok,
            "required_mm": scan.required_mm,
            "placement_ok": scan.placement_ok,
            "issues": scan.issues,
            "created_at": scan.created_at.isoformat(),
            "updated_at": scan.updated_at.isoformat(),
            "images": [
                {
                    "id": str(image.id),
                    "label": image.label,
                    "status": image.status,
                    "raw_text": image.raw_text,
                    "declarations": image.declarations,
                    "font_ok": image.font_ok,
                    "required_mm": image.required_mm,
                    "placement_ok": image.placement_ok,
                    "error_message": image.error_message,
                }
                for image in images
            ],
        }

    finally:
        session.close()


@app.get("/api/scans")
def get_scan_history(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
):
    if page < 1:
        raise HTTPException(
            status_code=422,
            detail="page must be at least 1",
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=422,
            detail="page_size must be between 1 and 100",
        )

    session = SessionLocal()

    try:
        count_statement = select(func.count()).select_from(Scan)

        if status is not None:
            count_statement = count_statement.where(
                Scan.status == status
            )

        total = session.execute(count_statement).scalar_one()

        statement = (
            select(Scan)
            .order_by(Scan.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        if status is not None:
            statement = statement.where(Scan.status == status)

        scans = session.execute(statement).scalars().all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": str(scan.id),
                    "status": scan.status,
                    "input_type": scan.input_type,
                    "product_name": scan.product_name,
                    "category": scan.category,
                    "created_at": scan.created_at.isoformat(),
                    "updated_at": scan.updated_at.isoformat(),
                }
                for scan in scans
            ],
        }

    finally:
        session.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )