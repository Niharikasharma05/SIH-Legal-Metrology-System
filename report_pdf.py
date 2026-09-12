"""Phase 5.2 — PDF compliance report generation.

Renders an HTML/CSS template from build_report_data()'s output and turns
it into PDF bytes via WeasyPrint. No template engine dependency (Jinja2
isn't in requirements.txt and this template is simple enough not to need
one) — plain str.format() with every dynamic value passed through
html.escape() first, since OCR-extracted text can legitimately contain
characters like '&' or '<' that would otherwise break the HTML.
"""

from typing import TYPE_CHECKING

import html

from weasyprint import HTML

from reporting import build_report_data

if TYPE_CHECKING:
    from models import Scan


STATUS_COLORS = {
    "COMPLIANT": "#1a7f37",
    "WARNING": "#9a6700",
    "VIOLATION": "#cf222e",
}
DEFAULT_STATUS_COLOR = "#57606a"  # pending/processing/failed — shouldn't normally reach a report


def _esc(value: str) -> str:
    return html.escape(str(value))


def _render_field_rows(declared_fields: list[dict]) -> str:
    rows = []

    for field in declared_fields:
        rows.append(
            f"<tr><td class='label'>{_esc(field['label'])}</td>"
            f"<td class='value'>{_esc(field['value'])}</td></tr>"
        )

    return "\n".join(rows)


def _render_issue_items(issues: list[str]) -> str:
    return "\n".join(f"<li>{_esc(issue)}</li>" for issue in issues)


def _render_html(data: dict) -> str:
    status_color = STATUS_COLORS.get(data["status"], DEFAULT_STATUS_COLOR)

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{ size: A4; margin: 2cm; }}
    body {{ font-family: sans-serif; color: #1f2328; font-size: 11pt; }}
    h1 {{ font-size: 16pt; margin-bottom: 4px; }}
    .subtitle {{ color: #57606a; margin-top: 0; margin-bottom: 20px; }}
    .status-badge {{
        display: inline-block; padding: 4px 12px; border-radius: 4px;
        color: white; font-weight: bold; background-color: {status_color};
    }}
    table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
    td {{ padding: 6px 8px; border-bottom: 1px solid #d0d7de; vertical-align: top; }}
    td.label {{ width: 40%; color: #57606a; }}
    td.value {{ font-weight: 500; }}
    h2 {{ font-size: 12pt; margin-top: 24px; margin-bottom: 8px; }}
    ul.issues {{ margin: 0; padding-left: 20px; }}
    ul.issues li {{ margin-bottom: 6px; }}
    .meta {{ color: #57606a; font-size: 9pt; margin-top: 32px; }}
</style>
</head>
<body>
    <h1>SetuCheck Legal Metrology Compliance Report</h1>
    <p class="subtitle">Product: {_esc(data['product_name'])} &middot; Category: {_esc(data['category'])}</p>

    <p><span class="status-badge">{_esc(data['status'])}</span></p>

    <h2>Declared Fields</h2>
    <table>
        {_render_field_rows(data['declared_fields'])}
    </table>

    <h2>Label Quality Checks</h2>
    <table>
        <tr><td class="label">Readability</td><td class="value">{_esc(data['readability'])}</td></tr>
        <tr><td class="label">Placement</td><td class="value">{_esc(data['placement'])}</td></tr>
    </table>

    <h2>Issues</h2>
    <ul class="issues">
        {_render_issue_items(data['issues'])}
    </ul>

    <p class="meta">
        Scan ID: {_esc(data['scan_id'])} &middot;
        Input type: {_esc(data['input_type'])} &middot;
        Scanned: {_esc(data['created_at'])}
    </p>
</body>
</html>
"""


def generate_pdf_report(scan: "Scan") -> bytes:
    """Build the compliance report for `scan` and return raw PDF bytes."""
    data = build_report_data(scan)
    html_str = _render_html(data)

    return HTML(string=html_str).write_pdf()