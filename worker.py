"""Phase 2 Postgres-backed scan worker."""

import os
import tempfile
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from db import SessionLocal
from models import Scan, ScanImage
from step1_preprocess import preprocess_image
from step2_ocr import extract_text_from_image
from step3_parser import parse_legal_metrology_declarations
from storage import download_image


PROCESSING_TIMEOUT = timedelta(minutes=15)
POLL_INTERVAL_SECONDS = 1


def recover_stale_processing() -> None:
    cutoff = datetime.now(timezone.utc) - PROCESSING_TIMEOUT

    session = SessionLocal()

    try:
        session.execute(
            update(ScanImage)
            .where(
                ScanImage.status == "processing",
                ScanImage.started_at.is_not(None),
                ScanImage.started_at < cutoff,
            )
            .values(
                status="pending",
                started_at=None,
            )
        )

        session.commit()

    finally:
        session.close()


def claim_image():
    session = SessionLocal()

    try:
        statement = (
            select(ScanImage)
            .where(ScanImage.status == "pending")
            .order_by(ScanImage.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )

        image = session.execute(statement).scalar_one_or_none()

        if image is None:
            session.rollback()
            return None

        image.status = "processing"
        image.started_at = datetime.now(timezone.utc)

        session.commit()

        return image.id

    finally:
        session.close()


def _merge_first_detected(images):
    keys = (
        "mrp",
        "net_quantity",
        "date_of_mfg",
        "manufacturer_address",
        "consumer_care",
    )

    merged = {}

    for key in keys:
        merged[key] = None

        for image in images:
            declarations = image.declarations or {}
            value = declarations.get(key)

            if value:
                merged[key] = value
                break

    return merged


def _build_parent_issues(declarations, font_ok, required_mm):
    issues = []

    if not declarations["mrp"]:
        issues.append(
            "Rule 6(1)(e): Retail sale price (MRP) not detected"
        )

    if not declarations["net_quantity"]:
        issues.append(
            "Rule 6(1)(c): Net quantity not detected"
        )

    if not declarations["date_of_mfg"]:
        issues.append(
            "Rule 6(1)(d): Month/year of manufacture not detected"
        )

    if not declarations["manufacturer_address"]:
        issues.append(
            "Rule 6(1)(a): Manufacturer/packer address not clearly detected"
        )

    if not declarations["consumer_care"]:
        issues.append(
            "Rule 6(2): Consumer care contact details not detected"
        )

    if font_ok is False:
        mm_note = (
            f" (Rule 7 requires min. {required_mm}mm for this quantity)"
            if required_mm
            else ""
        )

        issues.append(
            "Rule 7: Text may be smaller than the required numeral height"
            + mm_note
        )

    return issues


def _finalize_scan(session, scan_id) -> None:
    scan = session.get(Scan, scan_id)

    if scan is None:
        return

    images = session.execute(
        select(ScanImage)
        .where(ScanImage.scan_id == scan_id)
        .order_by(ScanImage.created_at)
    ).scalars().all()

    if not images:
        return

    terminal_statuses = {"done", "failed"}

    if any(image.status not in terminal_statuses for image in images):
        return

    if any(image.status == "failed" for image in images):
        scan.status = "failed"
        return

    declarations = _merge_first_detected(images)

    raw_text_parts = [
        image.raw_text
        for image in images
        if image.raw_text
    ]

    scan.raw_text = "\n\n".join(raw_text_parts)

    scan.mrp = declarations["mrp"]
    scan.net_quantity = declarations["net_quantity"]
    scan.date_of_mfg = declarations["date_of_mfg"]
    scan.manufacturer_address = declarations["manufacturer_address"]
    scan.consumer_care = declarations["consumer_care"]

    font_values = [
        image.font_ok
        for image in images
        if image.font_ok is not None
    ]

    if any(value is False for value in font_values):
        scan.font_ok = False
    elif any(value is True for value in font_values):
        scan.font_ok = True
    else:
        scan.font_ok = None

    required_mm_values = [
        image.required_mm
        for image in images
        if image.required_mm is not None
    ]

    scan.required_mm = (
        required_mm_values[0]
        if required_mm_values
        else None
    )

    placement_values = [
        image.placement_ok
        for image in images
        if image.placement_ok is not None
    ]

    scan.placement_ok = (
        placement_values[0]
        if placement_values
        else None
    )

    issues = _build_parent_issues(
        declarations,
        scan.font_ok,
        scan.required_mm,
    )

    scan.issues = issues

    has_mrp = declarations["mrp"] is not None
    has_qty = declarations["net_quantity"] is not None

    if not issues:
        scan.status = "COMPLIANT"
    elif not has_mrp or not has_qty:
        scan.status = "VIOLATION"
    else:
        scan.status = "WARNING"


def process_image(image_id) -> None:
    session = SessionLocal()

    try:
        image = session.get(ScanImage, image_id)

        if image is None:
            return

        object_key = image.object_key

        contents = download_image(object_key)

        extension = os.path.splitext(object_key)[1] or ".jpg"

        tmp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=extension,
            ) as tmp:
                tmp.write(contents)
                tmp_path = tmp.name

            resized, enhanced, _blur_score = preprocess_image(tmp_path)

            if enhanced is None:
                raise RuntimeError(
                    "Could not read the uploaded image"
                )

            raw_lines = extract_text_from_image(enhanced)

            parsed = parse_legal_metrology_declarations(raw_lines)

            image.raw_text = parsed["raw_text"]
            image.declarations = parsed["declarations"]
            image.font_ok = parsed["font_ok"]
            image.required_mm = parsed["required_mm"]
            image.placement_ok = None
            image.status = "done"
            image.processed_at = datetime.now(timezone.utc)
            image.error_message = None

            session.flush()

            _finalize_scan(session, image.scan_id)

            session.commit()

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as error:
        session.rollback()

        failed_session = SessionLocal()

        try:
            image = failed_session.get(ScanImage, image_id)

            if image is None:
                return

            image.attempts += 1
            image.error_message = str(error)

            if image.attempts >= 3:
                image.status = "failed"
                image.processed_at = datetime.now(timezone.utc)
            else:
                image.status = "pending"
                image.started_at = None

            failed_session.flush()

            _finalize_scan(failed_session, image.scan_id)

            failed_session.commit()

        finally:
            failed_session.close()

    finally:
        session.close()


def main():
    recover_stale_processing()

    while True:
        image_id = claim_image()

        if image_id is None:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        process_image(image_id)


if __name__ == "__main__":
    main()