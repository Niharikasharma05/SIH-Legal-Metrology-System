from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from step1_preprocess import preprocess_image
from step2_ocr import extract_text_from_image
from step3_parser import parse_legal_metrology_declarations

app = FastAPI(title="SIH Legal Metrology Verification API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Legal Metrology OCR API Active"}

@app.post("/api/v1/verify-package")
async def verify_package(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    temp_path = "temp_upload.jpg"
    cv2.imwrite(temp_path, image)

    resized, enhanced = preprocess_image(temp_path)
    ocr_results = extract_text_from_image(enhanced)
    compliance_report = parse_legal_metrology_declarations(ocr_results)

    return {
        "filename": file.filename,
        "compliance_summary": compliance_report,
        "ocr_details": ocr_results
    }