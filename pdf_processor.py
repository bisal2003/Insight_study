
import os
import pytesseract
from pdf2image import convert_from_path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

# Configure Poppler path (Windows)
POPPLER_PATH = r"C:\poppler\Library\bin"  # Update if extracted elsewhere

# Configure Tesseract (Uncomment for Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update if installed elsewhere

def extract_text_from_image(image):
    """Extract text from a single image"""
    try:
        return pytesseract.image_to_string(
            image, 
            config='--psm 6 -l eng',
            timeout=300
        )
    except Exception as e:
        return f"⚠️ OCR Error: {str(e)}"

def process_pdf(pdf_path, dpi=300):
    """Process PDF with proper Poppler configuration"""
    try:
        # Convert PDF to images
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            poppler_path=POPPLER_PATH,  # Explicit path
            thread_count=4,
            grayscale=True,  # Better for OCR
            fmt='jpeg'       # Smaller memory footprint
        )
        
        if not images:
            raise ValueError("PDF conversion failed - no pages extracted")

        # Process with progress tracking
        full_text = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i, img in enumerate(images):
                futures.append(executor.submit(
                    lambda x: (i+1, extract_text_from_image(x)), 
                    img
                ))
            
            for future in futures:
                page_num, text = future.result()
                full_text.append(f"=== Page {page_num} ===\n{text}")
        
        return "\n\n".join(full_text)
    
    except Exception as e:
        raise RuntimeError(
            f"Failed to process PDF. Please:\n"
            f"1. Ensure Poppler is installed at {POPPLER_PATH}\n"
            f"2. Check PDF is not password-protected\n"
            f"Error details: {str(e)}"
        )