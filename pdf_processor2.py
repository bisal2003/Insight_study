from pdf2image import convert_from_path
from paddleocr import PaddleOCR
import os

def process_pdf(pdf_path):
    """Extract text from a PDF using OCR."""
    
    # Convert PDF to images
    images = convert_from_path(pdf_path, dpi=300)  # Higher DPI for better OCR
    extracted_text = []

    # Create a directory for images if not exists
    os.makedirs("debug_images", exist_ok=True)

    # Initialize PaddleOCR
    ocr = PaddleOCR(lang="en")

    # Process each image
    for i, img in enumerate(images):
        image_path = f"debug_images/page_{i+1}.png"
        img.save(image_path, "PNG")  # Save for debugging

        # Perform OCR
        result = ocr.ocr(image_path, cls=True)

        # Extract text
        page_text = "\n".join([" ".join([word_info[1][0] for word_info in line]) for line in result if line])
        extracted_text.append(f"=== Page {i+1} ===\n{page_text}")

    return "\n\n".join(extracted_text)
