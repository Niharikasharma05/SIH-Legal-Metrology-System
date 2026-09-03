import re

def parse_legal_metrology_declarations(raw_lines):
    full_text = " ".join([item["text"] for item in raw_lines])
    
    # Regex patterns for mandatory declarations
    mrp_pattern = r"(?:MRP|M\.R\.P\.|Rs\.?|₹)\s*[:\.-]?\s*(\d+(?:\.\d{1,2})?)"
    net_wt_pattern = r"(?:Net\s*Wt|Net\s*Qty|Quantity|Net\s*Weight|NET\s*WT)\s*[:\.-]?\s*(\d+(?:\.\d+)?\s*(?:g|grm|gram|grams|kg|ml|l|liter|litres|N|units))"
    date_pattern = r"(?:Mfg|Packed|Pkg|Date|MFD|PKD)\s*[:\.-]?\s*(\d{2}[/\.-]\d{2}[/\.-]\d{2,4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{2,4})"
    fssai_pattern = r"(?:Lic\s*No\.?|Licence\s*No\.?|FSSAI)\s*[:\.-]?\s*(\d{14})"
    contact_pattern = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\d{10}|1800\s*\d{3}\s*\d{3,4})"

    mrp_match = re.search(mrp_pattern, full_text, re.IGNORECASE)
    net_wt_match = re.search(net_wt_pattern, full_text, re.IGNORECASE)
    date_match = re.search(date_pattern, full_text, re.IGNORECASE)
    fssai_match = re.search(fssai_pattern, full_text, re.IGNORECASE)
    contact_match = re.search(contact_pattern, full_text, re.IGNORECASE)

    declarations = {
        "mrp": mrp_match.group(0) if mrp_match else None,
        "net_quantity": net_wt_match.group(0) if net_wt_match else None,
        "date_of_mfg": date_match.group(0) if date_match else None,
        "fssai_license": fssai_match.group(0) if fssai_match else None,
        "consumer_care": contact_match.group(0) if contact_match else None,
    }

    missing_fields = [k for k, v in declarations.items() if v is None]
    is_compliant = len(missing_fields) == 0

    return {
        "is_compliant": is_compliant,
        "declarations": declarations,
        "missing_fields": missing_fields,
        "raw_text": full_text
    }