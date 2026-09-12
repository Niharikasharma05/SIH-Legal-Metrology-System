"""Phase 4.3 — placement check.

Detects whether the required Legal Metrology declarations (MRP, net
quantity, manufacturer address, consumer care, date of manufacture) are
grouped together on the label or scattered across it, using
sklearn.cluster.DBSCAN on the bounding-box centroids of the OCR lines that
look like each declaration.

This intentionally reuses only the *keyword* half of step3_parser.py's
regex patterns (no value capture) — it only needs to know which raw OCR
line a declaration keyword appears on, not the declared value itself.
"""

import re

from sklearn.cluster import DBSCAN


# Keyword-only versions of the step3_parser.py patterns — deliberately kept
# in sync with that file's keyword lists. If you add a new declaration type
# there, add its keyword pattern here too.
DECLARATION_KEYWORD_PATTERNS = [
    r"MRP|M\.R\.P\.|Max(?:imum)?\s*Retail\s*Price",
    r"Net\s*Wt|Net\s*Qty|Net\s*Quantity|Net\s*Weight|Net\s*Volume|Net\s*Content|NET\s*WT\.?|Contents",
    r"Manufactured\s*by|Mfd\s*by|Mfg\s*by|Packed\s*by|Pkd\s*by|Imported\s*by|Imp\s*by|Marketed\s*by|Mkt\s*by|Mktd\s*by|Address",
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|1800\s*\d{3}\s*\d{3,4}",
    r"Date\s*of\s*Manufactur(?:e|ing)|Date\s*of\s*Import|Imp\.?\s*Date|Mfg\.?\s*Date|MFD|PKD",
]

_COMBINED_PATTERN = re.compile("|".join(DECLARATION_KEYWORD_PATTERNS), re.IGNORECASE)

# DBSCAN radius, expressed as a multiple of the label's median OCR text
# height rather than a fixed pixel count — a fixed pixel radius would be
# meaningless across different photo resolutions/distances, but text
# height stays roughly proportional to how "close together" two lines
# look on the physical label. This multiplier is an assumption, not a
# measured constant — tune it against real label photos.
EPS_TEXT_HEIGHT_MULTIPLIER = 15
DEFAULT_EPS_PX = 100  # fallback when no text height could be measured


def _bbox_center(bbox: list) -> tuple[float, float] | None:
    if len(bbox) != 4:
        return None

    x_center = sum(pt[0] for pt in bbox) / 4
    y_center = sum(pt[1] for pt in bbox) / 4

    return x_center, y_center


def _bbox_height(bbox: list) -> float | None:
    if len(bbox) != 4:
        return None

    ys = [pt[1] for pt in bbox]

    return max(ys) - min(ys)


def check_placement(raw_lines: list[dict]) -> dict:
    """Return {'placement_ok': bool | None, 'declaration_line_count': int,
    'num_clusters': int | None}.

    placement_ok is None (not False) when fewer than 2 declaration-looking
    lines were found — with 0 or 1 such lines there's nothing to judge
    "grouped vs scattered" against, so this is a "can't tell" case, not a
    failure, consistent with how other checks in this codebase skip rather
    than guess when there isn't enough to compare.
    """
    heights = [
        h for h in (_bbox_height(item.get("bbox", [])) for item in raw_lines)
        if h is not None
    ]
    median_height = sorted(heights)[len(heights) // 2] if heights else None
    eps = (
        median_height * EPS_TEXT_HEIGHT_MULTIPLIER
        if median_height
        else DEFAULT_EPS_PX
    )

    points = []

    for item in raw_lines:
        text = item.get("text", "")

        if not _COMBINED_PATTERN.search(text):
            continue

        center = _bbox_center(item.get("bbox", []))

        if center is not None:
            points.append(center)

    if len(points) < 2:
        return {
            "placement_ok": None,
            "declaration_line_count": len(points),
            "num_clusters": None,
        }

    # min_samples=1: every declaration line belongs to *some* cluster, even
    # a cluster of one — an isolated declaration line far from the others
    # should count as its own cluster (i.e. "scattered"), not get thrown
    # away as unclustered noise the way a larger min_samples would.
    labels = DBSCAN(eps=eps, min_samples=1).fit(points).labels_
    num_clusters = len(set(labels))

    return {
        "placement_ok": num_clusters == 1,
        "declaration_line_count": len(points),
        "num_clusters": num_clusters,
    }