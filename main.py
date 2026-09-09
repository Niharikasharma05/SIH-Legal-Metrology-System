import tempfile, os, itertools, datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from step1_preprocess import preprocess_image
from step2_ocr import extract_text_from_image
from step3_parser import parse_legal_metrology_declarations

app = FastAPI(title="SetuCheck Legal Metrology Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_scan_id_counter = itertools.count(1001)


class ProductScan(BaseModel):
    id: int
    scannedAt: str
    productName: str
    mrp: str
    netQuantity: str
    manufactureDate: str
    manufacturerAddress: str
    consumerCare: str
    fontCheck: str
    status: str
    issues: List[str]
    rawText: str


@app.get("/health")
async def health():
    return {"status": "ok"}


def build_scan_result(declarations, font_ok, required_mm, issues, product_name, raw_text) -> ProductScan:
    has_mrp = declarations["mrp"] is not None
    has_qty = declarations["net_quantity"] is not None

    if not issues:
        status = "COMPLIANT"
    elif not has_mrp or not has_qty:
        status = "VIOLATION"
    else:
        status = "WARNING"

    font_text = "Readable"
    if not font_ok:
        font_text = f"Below Rule 7 minimum ({required_mm}mm)" if required_mm else "Too small — needs review"

    return ProductScan(
        id=next(_scan_id_counter),
        scannedAt=datetime.datetime.now().isoformat(),
        productName=product_name or "Untitled scan",
        mrp=declarations["mrp"] or "Not detected",
        netQuantity=declarations["net_quantity"] or "Not detected",
        manufactureDate=declarations["date_of_mfg"] or "Not detected",
        manufacturerAddress="Present" if declarations["manufacturer_address"] else "Missing",
        consumerCare="Present" if declarations["consumer_care"] else "Missing",
        fontCheck=font_text,
        status=status,
        issues=issues,
        rawText=raw_text,
    )


@app.post("/api/compliance/scans", response_model=ProductScan)
async def scan_compliance(
    file: Optional[UploadFile] = File(None),
    productName: Optional[str] = Form(None),
):
    empty_declarations = {
        "mrp": None, "net_quantity": None, "date_of_mfg": None,
        "manufacturer_address": None, "consumer_care": None,
    }

    if not file or not file.filename:
        return build_scan_result(
            empty_declarations, False, None,
            ["No image received by the server"], productName, "",
        )

    contents = await file.read()
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        resized, enhanced, blur_score = preprocess_image(tmp_path)
        if enhanced is None:
            return build_scan_result(
                empty_declarations, False, None,
                ["Could not read the uploaded image"], productName, "",
            )

        raw_lines = extract_text_from_image(enhanced)
        parsed = parse_legal_metrology_declarations(raw_lines)

        issues = parsed["issues"]
        if blur_score is not None and blur_score < 40:
            issues = ["Image appears blurry — hold steady and retake for reliable results"] + issues

        return build_scan_result(
            parsed["declarations"],
            parsed["font_ok"],
            parsed["required_mm"],
            issues,
            productName,
            parsed["raw_text"],
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/api/compliance/scans", response_model=List[ProductScan])
async def get_scan_history():
    return []


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)