"""Phase 5.1 — shared report-data builder.

Both the PDF renderer (5.2, WeasyPrint) and the DOCX renderer (5.3,
python-docx) consume the same dict from build_report_data() so field
formatting/fallback text is defined exactly once, not twice.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import Scan


NOT_DETECTED = "Not detected"


def _display(value: str | None) -> str:
    """String/text fields: None means the parser never found it on the
    label/listing — surface that as an explicit gap, not a blank cell."""
    return value if value else NOT_DETECTED


def _display_bool(value: bool | None, true_text: str, false_text: str) -> str:
    """Boolean checks (font_ok, placement_ok): None here means the check
    didn't run at all (e.g. a Phase 6 listing-mode scan has no photo, so
    there's nothing to check readability/placement on) — that's a
    different situation from a string field never being detected, so it
    gets its own wording rather than reusing NOT_DETECTED.
    """
    if value is None:
        return "Not applicable"

    return true_text if value else false_text


def build_report_data(scan: "Scan") -> dict:
    """Return a fully-formatted dict ready for template/document rendering.
    No None values reach the caller — every field is already a display
    string, so 5.2/5.3 do no formatting logic of their own.
    """
    declared_fields = [
        {"label": "Maximum Retail Price (MRP)", "value": _display(scan.mrp)},
        {"label": "Net Quantity", "value": _display(scan.net_quantity)},
        {"label": "Unit Price", "value": _display(scan.unit_price)},
        {"label": "Discount Claim", "value": _display(scan.discount_claim)},
        {"label": "Free Quantity Claim", "value": _display(scan.free_qty_claim)},
        {"label": "Date of Manufacture", "value": _display(scan.date_of_mfg)},
        {"label": "Manufacturer/Packer Address", "value": _display(scan.manufacturer_address)},
        {"label": "Consumer Care Details", "value": _display(scan.consumer_care)},
    ]

    issues = list(scan.issues) if scan.issues else []

    return {
        "scan_id": str(scan.id),
        "product_name": _display(scan.product_name),
        "category": _display(scan.category),
        "input_type": scan.input_type,
        "created_at": scan.created_at.strftime("%d %b %Y, %H:%M %Z").strip(),
        "status": scan.status,
        "declared_fields": declared_fields,
        "readability": _display_bool(
            scan.font_ok,
            true_text="Passed readability heuristic",
            false_text="Failed readability heuristic (see issues below)",
        ),
        "placement": _display_bool(
            scan.placement_ok,
            true_text="Declarations grouped together",
            false_text="Declarations scattered across the label (see issues below)",
        ),
        "issues": issues if issues else ["No issues detected"],
    }