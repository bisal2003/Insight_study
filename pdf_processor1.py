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


# import fitz  # PyMuPDF
# import io
# from PIL import Image
# import concurrent.futures
# import re
# import os
# from paddleocr import PaddleOCR

# # Initialize PaddleOCR
# ocr = PaddleOCR(use_angle_cls=True, lang="en")

# # Ensure debug folder exists
# DEBUG_FOLDER = "debug_images"
# os.makedirs(DEBUG_FOLDER, exist_ok=True)

# def extract_text_from_image(img, page_num):
#     """Extract text from image using PaddleOCR with debugging."""
#     try:
#         # Save raw image for debugging
#         raw_debug_path = os.path.join(DEBUG_FOLDER, f"raw_page_{page_num}.png")
#         img.save(raw_debug_path)
#         print(f"📷 Saved raw image: {raw_debug_path}")

#         # Convert PIL Image to numpy array
#         text_results = ocr.ocr(img)

#         # Extract and clean text
#         text = "\n".join([line[1][0] for result in text_results for line in result])

#         print(f"\n📝 OCR Extracted Text from Page {page_num}:\n", text[:500])
#         return clean_ocr_text(text) if text.strip() else "[OCR Failed: No readable text found]"
    
#     except Exception as e:
#         return f"[OCR Error: {str(e)}]"

# def clean_ocr_text(text):
#     """Basic cleaning of OCR artifacts."""
#     text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)  # Fix hyphenated line breaks
#     replacements = {'|': 'I', '@': 'a', '¢': 'c', '©': 'e'}
#     for wrong, right in replacements.items():
#         text = text.replace(wrong, right)
#     return text.strip()

# def process_pdf(pdf_path, dpi=300):
#     """Extract text from PDF using PyMuPDF and PaddleOCR."""
#     try:
#         doc = fitz.open(pdf_path)
#         if len(doc) > 30:
#             raise ValueError("Document too large (max 30 pages)")
        
#         full_text = []
#         with concurrent.futures.ThreadPoolExecutor() as executor:
#             futures = []
#             for page_num, page in enumerate(doc, start=1):
#                 pix = page.get_pixmap(dpi=dpi)

#                 # Convert PyMuPDF Pixmap to PIL Image
#                 img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

#                 # Save image for debugging
#                 debug_img_path = os.path.join(DEBUG_FOLDER, f"pdf_to_image_page_{page_num}.png")
#                 img.save(debug_img_path)
#                 print(f"📄 Saved PDF-rendered image: {debug_img_path}")

#                 futures.append(executor.submit(
#                     lambda x: (page_num, extract_text_from_image(x, page_num)),  
#                     img
#                 ))
            
#             for future in concurrent.futures.as_completed(futures):
#                 page_num, text = future.result()
#                 if not text.startswith('[OCR Failed]'):
#                     full_text.append(f"=== Page {page_num} ===\n{text}\n")
        
#         if not full_text:
#             raise RuntimeError("No readable text found in any pages")
            
#         return "\n".join(full_text)
    
#     except Exception as e:
#         raise RuntimeError(f"PDF processing failed: {str(e)}")



# import fitz  # PyMuPDF
# import io
# import pytesseract
# from PIL import Image, ImageEnhance
# import concurrent.futures
# import re
# import os

# # Ensure debug folder exists
# DEBUG_FOLDER = "debug_images"
# os.makedirs(DEBUG_FOLDER, exist_ok=True)

# def preprocess_image(img, page_num):
#     """Enhance image for better OCR results."""
#     img = img.convert('L')  # Convert to grayscale
    
#     # Apply contrast enhancement
#     enhancer = ImageEnhance.Contrast(img)
#     img = enhancer.enhance(2.0)  # Increase contrast

#     # Save preprocessed image for debugging
#     debug_path = os.path.join(DEBUG_FOLDER, f"processed_page_{page_num}.png")
#     img.save(debug_path)
#     print(f"🛠 Saved preprocessed image: {debug_path}")

#     return img.point(lambda x: 0 if x < 140 else 255)

# def extract_text_from_image(img, page_num):
#     """Extract text from image using OCR with debugging."""
#     try:
#         # Save original image for debugging
#         raw_debug_path = os.path.join(DEBUG_FOLDER, f"raw_page_{page_num}.png")
#         img.save(raw_debug_path)
#         print(f"📷 Saved raw image: {raw_debug_path}")

#         # Preprocess image
#         processed_img = preprocess_image(img, page_num)

#         # Try different OCR configurations
#         for config in ['--psm 6 -l eng', '--psm 11 -l eng', '--psm 4 -l eng']:
#             try:
#                 text = pytesseract.image_to_string(processed_img, config=config, timeout=15)
                
#                 # Print extracted text for debugging
#                 print(f"\n📝 OCR Extracted Text from Page {page_num} (Config: {config}):\n", text[:500])

#                 if len(text.strip()) > 5:  # Valid text check
#                     return clean_ocr_text(text)
#             except Exception as e:
#                 print(f"⚠️ OCR failed on page {page_num} with config {config}: {e}")
        
#         return "[OCR Failed: No readable text found]"
#     except Exception as e:
#         return f"[OCR Error: {str(e)}]"

# def clean_ocr_text(text):
#     """Basic cleaning of OCR artifacts."""
#     # Remove hyphenated line breaks
#     text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)

#     # Fix common OCR mistakes
#     replacements = {'|': 'I', '@': 'a', '¢': 'c', '©': 'e'}
#     for wrong, right in replacements.items():
#         text = text.replace(wrong, right)

#     return text.strip()

# def process_pdf(pdf_path, dpi=300):
#     """Extract text from PDF using PyMuPDF."""
#     try:
#         doc = fitz.open(pdf_path)
#         if len(doc) > 30:
#             raise ValueError("Document too large (max 30 pages)")
        
#         full_text = []
#         with concurrent.futures.ThreadPoolExecutor() as executor:
#             futures = []
#             for page_num, page in enumerate(doc, start=1):
#                 pix = page.get_pixmap(dpi=dpi)

#                 # Convert PyMuPDF Pixmap to PIL Image
#                 img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

#                 # Save image for debugging
#                 debug_img_path = os.path.join(DEBUG_FOLDER, f"pdf_to_image_page_{page_num}.png")
#                 img.save(debug_img_path)
#                 print(f"📄 Saved PDF-rendered image: {debug_img_path}")

#                 futures.append(executor.submit(
#                     lambda x: (page_num, extract_text_from_image(x, page_num)),  
#                     img
#                 ))
            
#             for future in concurrent.futures.as_completed(futures):
#                 page_num, text = future.result()
#                 if not text.startswith('[OCR Failed]'):
#                     full_text.append(f"=== Page {page_num} ===\n{text}\n")
        
#         if not full_text:
#             raise RuntimeError("No readable text found in any pages")
            
#         return "\n".join(full_text)
    
#     except Exception as e:
#         raise RuntimeError(f"PDF processing failed: {str(e)}")

