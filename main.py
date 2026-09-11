import os
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db import SessionLocal
from models import Scan, ScanImage
from settings import settings
from storage import ensure_bucket, image_object_key, upload_image


async def _read_upload(file: UploadFile) -> bytes:
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image upload")
    return contents


def _extension(filename: str | None) -> str:
    if not filename:
        return "jpg"
    extension = os.path.splitext(filename)[1].lower().lstrip(".")
    return extension or "jpg"


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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ALLOWED_LABELS = {"front", "back", "side", "other"}


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
):
    if not 1 <= len(files) <= 4:
        raise HTTPException(
            status_code=400,
            detail="A scan must contain between 1 and 4 images",
        )

    if labels is None:
        labels = ["other"] * len(files)
    elif len(labels) != len(files):
        raise HTTPException(
            status_code=400,
            detail="The number of labels must match the number of images",
        )

    invalid_labels = [
        label for label in labels
        if label not in ALLOWED_LABELS
    ]

    if invalid_labels:
        raise HTTPException(
            status_code=400,
            detail="Invalid image label",
        )

    image_payloads = []

    for file in files:
        image_payloads.append(
            (
                file,
                await _read_upload(file),
                _extension(file.filename),
            )
        )

    session = SessionLocal()

    try:
        scan = Scan(
            input_type="image",
            status="pending",
            product_name=product_name,
        )

        session.add(scan)
        session.flush()

        image_count = 0

        for (file, contents, extension), label in zip(
            image_payloads,
            labels,
        ):
            image_id = uuid.uuid4()

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
                label=label,
                status="pending",
                attempts=0,
            )

            session.add(image)
            image_count += 1

        session.commit()

        return JSONResponse(
            status_code=202,
            content={
                "id": str(scan.id),
                "status": scan.status,
                "image_count": image_count,
            },
        )

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.get("/api/scans/{scan_id}")
def get_scan(scan_id: str):
    session = SessionLocal()

    try:
        try:
            scan_uuid = uuid.UUID(scan_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid scan id",
            )

        statement = (
            select(Scan)
            .where(Scan.id == scan_uuid)
            .options(selectinload(Scan.images))
        )

        scan = session.execute(statement).scalar_one_or_none()

        if scan is None:
            raise HTTPException(
                status_code=404,
                detail="Scan not found",
            )

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
                    "attempts": image.attempts,
                    "raw_text": image.raw_text,
                    "declarations": image.declarations,
                    "font_ok": image.font_ok,
                    "required_mm": image.required_mm,
                    "placement_ok": image.placement_ok,
                    "started_at": (
                        image.started_at.isoformat()
                        if image.started_at
                        else None
                    ),
                    "processed_at": (
                        image.processed_at.isoformat()
                        if image.processed_at
                        else None
                    ),
                    "error_message": image.error_message,
                    "created_at": image.created_at.isoformat(),
                }
                for image in scan.images
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
            status_code=400,
            detail="page must be at least 1",
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail="page_size must be between 1 and 100",
        )

    session = SessionLocal()

    try:
        statement = select(Scan).order_by(Scan.created_at.desc())

        if status is not None:
            statement = statement.where(Scan.status == status)

        offset = (page - 1) * page_size

        scans = session.execute(
            statement.offset(offset).limit(page_size)
        ).scalars().all()

        return {
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": str(scan.id),
                    "status": scan.status,
                    "input_type": scan.input_type,
                    "product_name": scan.product_name,
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