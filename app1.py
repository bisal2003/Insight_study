import streamlit as st
from pdf_processor1 import process_pdf
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyDMCXugVyrMIFP4KH1DJ56uBE6wMDWODgc"  # Replace with your API key
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("📄 PDF Text Extractor with OCR & AI Refinement")

# Upload PDF file
uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file:
    st.success("✅ PDF uploaded successfully!")

    # Save uploaded file
    pdf_path = "uploaded_pdf.pdf"
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Process PDF
    with st.spinner("Processing PDF... ⏳"):
        extracted_text = process_pdf(pdf_path)

    # Refine extracted text using Gemini
    with st.spinner("Refining extracted text with AI... 🤖"):
        prompt = (
            "Refine the following OCR-extracted text to improve readability. Ensure proper question numbering, marks distribution, "
            "and remove any noise. Structure it like a well-formatted question paper:\n\n"
            f"{extracted_text}"
        )
        response = model.generate_content(prompt)
        refined_text = response.text

    # Display results
    st.subheader("📃 Extracted Text:")
    st.text_area("Extracted Text (Refined):", refined_text, height=300)

    # Save to file option
    if st.button("💾 Save to Text File"):
        with open("refined_text.txt", "w", encoding="utf-8") as f:
            f.write(refined_text)
        st.success("✅ Text saved as `refined_text.txt`!")


# import streamlit as st
# from pdf_processor1 import process_pdf

# st.title("📄 PDF Text Extractor with OCR")

# # Upload PDF file
# uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

# if uploaded_file:
#     st.success("✅ PDF uploaded successfully!")

#     # Save uploaded file
#     pdf_path = "uploaded_pdf.pdf"
#     with open(pdf_path, "wb") as f:
#         f.write(uploaded_file.getbuffer())

#     # Process PDF
#     with st.spinner("Processing PDF... ⏳"):
#         extracted_text = process_pdf(pdf_path)

#     # Display results
#     st.subheader("📃 Extracted Text:")
#     st.text_area("Extracted Text:", extracted_text, height=300)

#     # Save to file option
#     if st.button("💾 Save to Text File"):
#         with open("extracted_text.txt", "w", encoding="utf-8") as f:
#             f.write(extracted_text)
#         st.success("✅ Text saved as `extracted_text.txt`!")


# import streamlit as st
# import os
# import time
# from pdf_processor1 import process_pdf
# import google.generativeai as genai

# # Configuration
# UPLOAD_FOLDER = "uploads"
# OUTPUT_FOLDER = "outputs"
# MAX_FILE_SIZE = 100  # MB
# MAX_PAGES = 30
# GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # Replace with your API key

# # Initialize Gemini
# genai.configure(api_key=GEMINI_API_KEY)
# model = genai.GenerativeModel('gemini-1.5-flash')

# # Create directories
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# st.set_page_config(
#     page_title="PDF Text Extractor Pro",
#     page_icon="📄",
#     layout="wide"
# )

# def validate_ocr_result(text):
#     """Check if OCR produced meaningful output."""
#     if not text.strip():
#         print("🚨 OCR output is empty!")
#         return False

#     # Print first 500 characters for debugging
#     print("🔍 OCR Extracted Raw Text:\n", text[:500])

#     error_lines = sum(1 for line in text.split('\n') if line.startswith('[OCR'))
#     return error_lines / len(text.split('\n')) < 0.5

# def main():
#     st.title("📄 Smart PDF to Text Converter")
#     st.markdown("Extract and enhance text from scanned PDFs using AI")

#     dpi = st.slider("Scan Quality (DPI)", 200, 400, 300, help="Higher DPI = better accuracy but slower processing")

#     uploaded_file = st.file_uploader("Upload your PDF (max 30 pages)", type=["pdf"], accept_multiple_files=False)

#     if uploaded_file:
#         file_size = uploaded_file.size / (1024 * 1024)
#         if file_size > MAX_FILE_SIZE:
#             st.error(f"❌ File size exceeds {MAX_FILE_SIZE}MB limit")
#             return
        
#         file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
#         with open(file_path, "wb") as f:
#             f.write(uploaded_file.getbuffer())
        
#         with st.status("Processing...", expanded=True) as status:
#             try:
#                 st.write("🔍 Extracting text from PDF...")
#                 start_time = time.time()
                
#                 # Process PDF
#                 raw_text = process_pdf(file_path, dpi=dpi)

#                 # Validate OCR results
#                 if not validate_ocr_result(raw_text):
#                     st.warning("OCR did not extract any meaningful text. Try increasing DPI or using a clearer PDF.")
#                     st.stop()

#                 output_filename = f"{os.path.splitext(uploaded_file.name)[0]}_extracted.txt"
#                 output_path = os.path.join(OUTPUT_FOLDER, output_filename)
#                 with open(output_path, "w", encoding="utf-8") as f:
#                     f.write(raw_text)
                
#                 processing_time = time.time() - start_time
#                 status.update(label=f"✅ Processed {len(raw_text.split('==='))-1} pages in {processing_time:.1f}s", state="complete", expanded=False)

#                 st.success("Text extraction complete!")
#                 st.text_area("Extracted Text", value=raw_text[:3000] + ("..." if len(raw_text)>3000 else ""), height=400)

#                 st.download_button("💾 Download Full Text", data=raw_text, file_name=output_filename, mime="text/plain")

#             except Exception as e:
#                 status.update(label="❌ Processing Failed", state="error", expanded=False)
#                 st.error(f"Error: {str(e)}")

# if __name__ == "__main__":
#     main()



# import streamlit as st
# import os
# import time
# from pdf_processor1 import process_pdf
# import google.generativeai as genai
# from PIL import Image
# import io

# # Configuration
# UPLOAD_FOLDER = "uploads"
# OUTPUT_FOLDER = "outputs"
# MAX_FILE_SIZE = 100  # MB
# MAX_PAGES = 30
# GEMINI_API_KEY = "AIzaSyDMCXugVyrMIFP4KH1DJ56uBE6wMDWODgc"  # Replace with your key

# # Initialize Gemini
# genai.configure(api_key=GEMINI_API_KEY)
# model = genai.GenerativeModel('gemini-1.5-flash')

# # Create directories
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# st.set_page_config(
#     page_title="PDF Text Extractor Pro",
#     page_icon="📄",
#     layout="wide"
# )

# def validate_ocr_result(text):
#     """Check if OCR produced meaningful output"""
#     if not text.strip():
#         return False
#     # Check if most lines are error messages
#     error_lines = sum(1 for line in text.split('\n') if line.startswith('[OCR'))
#     return error_lines / len(text.split('\n')) < 0.5  # Less than 50% errors

# def refine_text_with_gemini(raw_text):
#     """Enhanced text refinement with chunking and validation"""
#     if not validate_ocr_result(raw_text):
#         raise ValueError("No valid text to refine - OCR may have failed completely")
    
#     # Process in chunks to handle large documents
#     chunk_size = 10000
#     chunks = [raw_text[i:i+chunk_size] for i in range(0, len(raw_text), chunk_size)]
#     refined_text = []
    
#     progress_bar = st.progress(0)
#     for i, chunk in enumerate(chunks):
#         try:
#             prompt = f"""
#             Refine this OCR text while preserving:
#             1. Technical terms and mathematical notation
#             2. Original document structure
#             3. Page numbers and section headers

#             Common fixes needed:
#             - Correct broken words (e.g., 'inter national' → 'international')
#             - Fix digit/letter confusion (e.g., 'O' vs '0', 'l' vs '1')
#             - Remove scanner artifacts while keeping genuine symbols

#             Problematic Input:
#             {chunk}

#             Refined Output:"""
            
#             response = model.generate_content(
#                 prompt,
#                 generation_config={
#                     "max_output_tokens": 8000,
#                     "temperature": 0.2
#                 }
#             )
#             refined_text.append(response.text)
#         except Exception as e:
#             st.warning(f"Gemini refinement failed for chunk {i+1}: {str(e)}")
#             refined_text.append(chunk)  # Fallback to original
        
#         progress_bar.progress((i + 1) / len(chunks))
    
#     return "\n".join(refined_text)

# def main():
#     st.title("📄 Smart PDF to Text Converter")
#     st.markdown("Extract and enhance text from scanned PDFs using AI")
    
#     with st.expander("⚙️ Settings", expanded=True):
#         col1, col2 = st.columns(2)
#         with col1:
#             use_gemini = st.checkbox("Enable AI Text Refinement", True)
#         with col2:
#             dpi = st.slider("Scan Quality (DPI)", 200, 400, 300, help="Higher DPI = better accuracy but slower processing")
    
#     uploaded_file = st.file_uploader(
#         "Upload your PDF (max 30 pages)",
#         type=["pdf"],
#         accept_multiple_files=False,
#         help="For best results, use text-heavy documents with clear printing"
#     )
    
#     if uploaded_file:
#         # File validation
#         file_size = uploaded_file.size / (1024 * 1024)
#         if file_size > MAX_FILE_SIZE:
#             st.error(f"❌ File size exceeds {MAX_FILE_SIZE}MB limit")
#             return
        
#         # Save uploaded file
#         file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
#         with open(file_path, "wb") as f:
#             f.write(uploaded_file.getbuffer())
        
#         # Processing
#         with st.status("Processing...", expanded=True) as status:
#             try:
#                 st.write("🔍 Extracting text from PDF...")
#                 start_time = time.time()
                
#                 # Process PDF
#                 raw_text = process_pdf(file_path, dpi=dpi)
                
#                 # Validate OCR results
#                 if not validate_ocr_result(raw_text):
#                     raise RuntimeError("OCR failed to extract meaningful text. Try increasing DPI or upload a clearer PDF.")
                
#                 # AI refinement
#                 if use_gemini:
#                     st.write("🧠 Enhancing text with Gemini...")
#                     try:
#                         refined_text = refine_text_with_gemini(raw_text)
#                     except Exception as e:
#                         st.warning(f"AI refinement skipped: {str(e)}")
#                         refined_text = raw_text
#                 else:
#                     refined_text = raw_text
                
#                 # Save output
#                 output_filename = f"{os.path.splitext(uploaded_file.name)[0]}_extracted.txt"
#                 output_path = os.path.join(OUTPUT_FOLDER, output_filename)
#                 with open(output_path, "w", encoding="utf-8") as f:
#                     f.write(refined_text)
                
#                 processing_time = time.time() - start_time
#                 status.update(
#                     label=f"✅ Processed {len(raw_text.split('==='))-1} pages in {processing_time:.1f}s",
#                     state="complete",
#                     expanded=False
#                 )
                
#                 # Results
#                 st.success("Text extraction complete!")
#                 tab1, tab2 = st.tabs(["📄 Preview", "📊 Stats"])
                
#                 with tab1:
#                     st.text_area("Extracted Text", 
#                                value=refined_text[:3000] + ("..." if len(refined_text)>3000 else ""),
#                                height=400)
                
#                 with tab2:
#                     st.metric("Total Pages", len(raw_text.split('==='))-1)
#                     st.metric("Processing Time", f"{processing_time:.1f} seconds")
#                     st.metric("Text Quality", 
#                             "AI Enhanced" if use_gemini else "Raw OCR",
#                             help="AI-enhanced text has better formatting and accuracy")
                
#                 st.download_button(
#                     "💾 Download Full Text",
#                     data=refined_text,
#                     file_name=output_filename,
#                     mime="text/plain",
#                     type="primary"
#                 )
                
#             except Exception as e:
#                 status.update(
#                     label="❌ Processing Failed",
#                     state="error",
#                     expanded=False
#                 )
#                 st.error(f"Error: {str(e)}")
#                 st.markdown("""
#                 **Troubleshooting Tips:**
#                 - Try a higher DPI setting (400)
#                 - Ensure the PDF is not password protected
#                 - Upload a clearer scan with proper contrast
#                 - Disable AI refinement for highly technical documents
#                 """)
#                 st.stop()

# if __name__ == "__main__":
#     main()