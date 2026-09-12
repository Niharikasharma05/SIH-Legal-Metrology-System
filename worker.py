"""Phase 2 scan worker."""

import os
import tempfile
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from db import SessionLocal
from models import Scan, ScanImage
from step1_preprocess import preprocess_image
from step2_ocr import extract_text_from_image
from step3_parser import parse_legal_metrology_declarations
from step4_placement import check_placement
from storage import download_image


PROCESSING_TIMEOUT = timedelta(minutes=15)
POLL_INTERVAL_SECONDS = 2


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def recover_stale_processing() -> None:
    """Return processing images older than the timeout to pending."""
    cutoff = now_utc() - PROCESSING_TIMEOUT

    session = SessionLocal()

    try:
        stale_images = session.execute(
            select(ScanImage).where(
                ScanImage.status == "processing",
                ScanImage.started_at.is_not(None),
                ScanImage.started_at < cutoff,
            )
        ).scalars().all()

        for image in stale_images:
            image.status = "pending"
            image.started_at = None

        session.commit()
    finally:
        session.close()


def claim_image():
    """Atomically claim one pending image."""
    session = SessionLocal()

    try:
        image = session.execute(
            select(ScanImage)
            .where(ScanImage.status == "pending")
            .order_by(ScanImage.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        ).scalar_one_or_none()

        if image is None:
            session.rollback()
            return None

        image.status = "processing"
        image.started_at = now_utc()

        session.commit()

        return image.id
    finally:
        session.close()


def merge_declarations(images: list[ScanImage]) -> dict:
    """Take the first detected value for each declaration field."""
    fields = (
        "mrp",
        "net_quantity",
        "unit_price",
        "discount_claim",
        "free_qty_claim",
        "date_of_mfg",
        "manufacturer_address",
        "consumer_care",
        "mrp_value",
        "net_quantity_value",
        "net_quantity_unit",
        "unit_price_value",
        "unit_price_basis",
        "discount_pct_value",
        "free_qty_value",
        "free_qty_unit",
    )

    merged = {field: None for field in fields}

    for field in fields:
        for image in images:
            declarations = image.declarations or {}
            value = declarations.get(field)

            if value is not None:
                merged[field] = value
                break

    return merged


def build_missing_issues(
    declarations: dict,
    font_ok: bool | None,
    required_mm: float | None,
    placement_ok: bool | None = None,
) -> list[str]:
    """Compute parent-level compliance issues after declaration merge."""
    issues = []

    if declarations["mrp"] is None:
        issues.append(
            "Rule 6(1)(e): Retail sale price (MRP) not detected"
        )

    if declarations["net_quantity"] is None:
        issues.append(
            "Rule 6(1)(c): Net quantity not detected"
        )

    if declarations["date_of_mfg"] is None:
        issues.append(
            "Rule 6(1)(d): Month/year of manufacture not detected"
        )

    if declarations["manufacturer_address"] is None:
        issues.append(
            "Rule 6(1)(a): Manufacturer/packer address not clearly detected"
        )

    if declarations["consumer_care"] is None:
        issues.append(
            "Rule 6(2): Consumer care contact details not detected"
        )

    if font_ok is False:
        mm_note = (
            f" (Rule 7 would require {required_mm}mm for this quantity, "
            "but this check does not measure physical mm)"
            if required_mm
            else ""
        )
        issues.append(
            "Readability heuristic: detected text is smaller than a "
            "general legibility threshold — a relative pixel-based "
            "estimate, not a measured Rule 7 numeral-height verdict"
            + mm_note
        )

    if placement_ok is False:
        issues.append(
            "Required declarations are not grouped together in a single "
            "area of the label"
        )

    return issues


def _normalize_quantity(value: float, unit: str) -> tuple[str | None, float | None]:
    """Convert a (value, unit) pair to a (family, base_amount) tuple.

    family is 'weight' (base=grams), 'volume' (base=ml), or 'count'
    (base=item count). Returns (None, None) for an unrecognized unit.
    """
    unit = unit.lower()

    weight = {"g": 1, "grm": 1, "gram": 1, "grams": 1, "kg": 1000}
    volume = {"ml": 1, "l": 1000, "liter": 1000, "litres": 1000}
    count = {
        "n": 1, "u": 1, "unit": 1, "units": 1,
        "pc": 1, "pcs": 1, "piece": 1, "pieces": 1,
        "stick": 1, "sticks": 1, "tablet": 1, "tablets": 1,
        "capsule": 1, "capsules": 1,
    }

    if unit in weight:
        return "weight", value * weight[unit]
    if unit in volume:
        return "volume", value * volume[unit]
    if unit in count:
        return "count", value * count[unit]

    return None, None


def _normalize_basis(basis: str) -> tuple[str | None, float | None]:
    """Convert a unit-price basis (e.g. 'kg', '100g') to (family, base_amount)."""
    basis = basis.lower()

    weight_basis = {"g": 1, "kg": 1000, "100g": 100}
    volume_basis = {"ml": 1, "l": 1000, "litre": 1000, "liter": 1000}
    count_basis = {"unit": 1, "pc": 1, "piece": 1}

    if basis in weight_basis:
        return "weight", weight_basis[basis]
    if basis in volume_basis:
        return "volume", volume_basis[basis]
    if basis in count_basis:
        return "count", count_basis[basis]

    return None, None


# Relative tolerance for the MRP-vs-unit-price cross-check. OCR digits won't
# line up to the last paisa even on a fully compliant label, so this is a
# deliberate assumption, not a legal threshold from the PS — adjust freely.
UNIT_PRICE_TOLERANCE = 0.05


def check_misleading_declarations(declarations: dict) -> list[str]:
    """Phase 4.1b: cross-check declared values against each other.

    Both checks are skipped (not flagged) when there isn't enough
    structured data to compare safely — e.g. mismatched unit families,
    or a value simply wasn't detected. Absence of a discount/unit-price
    claim is never itself a violation (see step3_parser.py comment).
    """
    issues = []

    mrp = declarations.get("mrp_value")
    qty_val = declarations.get("net_quantity_value")
    qty_unit = declarations.get("net_quantity_unit")
    price_val = declarations.get("unit_price_value")
    price_basis = declarations.get("unit_price_basis")

    if None not in (mrp, qty_val, qty_unit, price_val, price_basis) and mrp > 0:
        qty_family, qty_base = _normalize_quantity(qty_val, qty_unit)
        basis_family, basis_amount = _normalize_basis(price_basis)

        if qty_family is not None and qty_family == basis_family and basis_amount:
            implied_total = price_val * (qty_base / basis_amount)
            relative_diff = abs(implied_total - mrp) / mrp

            if relative_diff > UNIT_PRICE_TOLERANCE:
                issues.append(
                    "Misleading declaration: declared unit price implies a "
                    f"total price of ~Rs.{implied_total:.2f}, which differs "
                    f"from the declared MRP of Rs.{mrp:.2f} by more than "
                    f"{int(UNIT_PRICE_TOLERANCE * 100)}%"
                )

    free_val = declarations.get("free_qty_value")
    free_unit = declarations.get("free_qty_unit")

    if None not in (free_val, free_unit, qty_val, qty_unit):
        free_family, free_base = _normalize_quantity(free_val, free_unit)
        qty_family, qty_base = _normalize_quantity(qty_val, qty_unit)

        if free_family is not None and free_family == qty_family and free_base >= qty_base:
            issues.append(
                "Misleading declaration: claimed 'free' quantity is not "
                "smaller than the total declared net quantity"
            )

    # NOTE: discount_pct_value is intentionally not cross-checked here.
    # Validating a "% off" claim needs an original/pre-discount price field
    # that doesn't exist anywhere in the current schema or parser output —
    # there's nothing to compare it against. Flagging this as a known gap
    # rather than inventing a second price field silently.

    return issues


# Relative tolerance for cross-image conflicts. Tighter than
# UNIT_PRICE_TOLERANCE because this compares the SAME printed number across
# two photos of the SAME pack (no unit-conversion arithmetic involved) — a
# real conflict should differ by more than plain OCR digit noise.
CROSS_IMAGE_TOLERANCE = 0.02


def check_cross_image_conflicts(images: list[ScanImage]) -> list[str]:
    """Phase 4.2: flag the same declared field reading differently across
    different images of the same scan (e.g. two photos of one pack showing
    different MRPs). Operates on each image's own `declarations` JSONB,
    not the already-merged dict, since the merge only keeps the first
    non-null value and would hide a disagreement.

    Comparisons are skipped (not flagged) when there's nothing to compare
    against, or when quantities are in genuinely incompatible unit
    families — same policy as check_misleading_declarations.
    """
    issues = []

    mrp_values = [
        value
        for image in images
        if (value := (image.declarations or {}).get("mrp_value")) is not None
    ]

    if len(mrp_values) >= 2:
        lo, hi = min(mrp_values), max(mrp_values)

        if lo > 0 and (hi - lo) / lo > CROSS_IMAGE_TOLERANCE:
            issues.append(
                "Misleading declaration: MRP reads differently across "
                f"images of the same product (Rs.{lo:.2f} vs Rs.{hi:.2f})"
            )

    qty_bases_by_family: dict[str, list[float]] = {}

    for image in images:
        declarations = image.declarations or {}
        value = declarations.get("net_quantity_value")
        unit = declarations.get("net_quantity_unit")

        if value is None or unit is None:
            continue

        family, base = _normalize_quantity(value, unit)

        if family is None:
            continue

        qty_bases_by_family.setdefault(family, []).append(base)

    for family, bases in qty_bases_by_family.items():
        if len(bases) < 2:
            continue

        lo, hi = min(bases), max(bases)

        if lo > 0 and (hi - lo) / lo > CROSS_IMAGE_TOLERANCE:
            issues.append(
                "Misleading declaration: net quantity reads differently "
                f"across images of the same product ({lo:g} vs {hi:g}, "
                f"{family} terms)"
            )

    return issues


def finalize_scan(
    session,
    scan: Scan,
    images: list[ScanImage],
) -> None:
    """Finalize the parent scan once all sibling images are terminal."""
    if any(image.status == "failed" for image in images):
        scan.status = "failed"
        return

    if any(image.status != "done" for image in images):
        return

    declarations = merge_declarations(images)

    scan.mrp = declarations["mrp"]
    scan.net_quantity = declarations["net_quantity"]
    scan.unit_price = declarations["unit_price"]
    scan.discount_claim = declarations["discount_claim"]
    scan.free_qty_claim = declarations["free_qty_claim"]
    scan.date_of_mfg = declarations["date_of_mfg"]
    scan.manufacturer_address = declarations["manufacturer_address"]
    scan.consumer_care = declarations["consumer_care"]

    scan.raw_text = "\n\n".join(
        image.raw_text
        for image in images
        if image.raw_text
    )

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

    if any(value is False for value in placement_values):
        scan.placement_ok = False
    elif any(value is True for value in placement_values):
        scan.placement_ok = True
    else:
        scan.placement_ok = None

    issues = build_missing_issues(
        declarations,
        scan.font_ok,
        scan.required_mm,
        scan.placement_ok,
    )

    misleading_issues = check_misleading_declarations(declarations)
    cross_image_issues = check_cross_image_conflicts(images)
    severity_issues = misleading_issues + cross_image_issues
    issues = issues + severity_issues

    scan.issues = issues

    if (
        declarations["mrp"] is None
        or declarations["net_quantity"] is None
        or severity_issues
    ):
        scan.status = "VIOLATION"
    elif issues:
        scan.status = "WARNING"
    else:
        scan.status = "COMPLIANT"


def process_image(image_id) -> None:
    """Process one claimed image and persist its result or failure."""
    session = SessionLocal()
    temp_path = None

    try:
        image = session.get(ScanImage, image_id)

        if image is None:
            return

        image_bytes = download_image(image.object_key)

        extension = os.path.splitext(image.object_key)[1] or ".jpg"

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:
            temp_file.write(image_bytes)
            temp_path = temp_file.name

        _, enhanced, _ = preprocess_image(temp_path)

        if enhanced is None:
            raise RuntimeError("Could not read the uploaded image")

        raw_lines = extract_text_from_image(enhanced)

        parsed = parse_legal_metrology_declarations(raw_lines)

        placement_result = check_placement(raw_lines)

        image.raw_text = parsed["raw_text"]
        image.declarations = parsed["declarations"]
        image.font_ok = parsed["font_ok"]
        image.required_mm = parsed["required_mm"]
        image.placement_ok = placement_result["placement_ok"]
        image.processed_at = now_utc()
        image.error_message = None
        image.status = "done"

        scan = session.get(Scan, image.scan_id)

        sibling_images = session.execute(
            select(ScanImage)
            .where(ScanImage.scan_id == image.scan_id)
            .order_by(ScanImage.created_at)
        ).scalars().all()

        if scan is not None:
            finalize_scan(session, scan, sibling_images)

        session.commit()

    except Exception as error:
        session.rollback()

        failure_session = SessionLocal()

        try:
            image = failure_session.get(ScanImage, image_id)

            if image is None:
                return

            image.attempts += 1
            image.error_message = str(error)

            if image.attempts >= 3:
                image.status = "failed"
                image.processed_at = now_utc()

                scan = failure_session.get(Scan, image.scan_id)

                if scan is not None:
                    scan.status = "failed"
            else:
                image.status = "pending"
                image.started_at = None

            failure_session.commit()
        finally:
            failure_session.close()

    finally:
        session.close()

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def main() -> None:
    recover_stale_processing()

    while True:
        image_id = claim_image()

        if image_id is None:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        process_image(image_id)


if __name__ == "__main__":
    main()