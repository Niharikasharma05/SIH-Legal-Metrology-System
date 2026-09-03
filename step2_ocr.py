import easyocr

reader = None

def get_ocr_reader():
    global reader
    if reader is None:
        # Load EasyOCR engine on CPU
        reader = easyocr.Reader(['en'], gpu=False)
    return reader

def extract_text_from_image(enhanced_image):
    ocr = get_ocr_reader()
    results = ocr.readtext(enhanced_image)
    
    extracted_lines = []
    for (bbox, text, confidence) in results:
        if confidence > 0.20:
            extracted_lines.append({
                "text": text,
                "confidence": round(float(confidence), 2),
                "bbox": [[int(pt[0]), int(pt[1])] for pt in bbox]
            })
    return extracted_lines