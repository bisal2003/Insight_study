# # app.py
# # Auto-generated file - update with your implementation


import streamlit as st
import os
import time
from pdf_processor1 import process_pdf

# Configuration
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
MAX_FILE_SIZE = 100  # MB

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

st.set_page_config(
    page_title="PDF Text Extractor",
    page_icon="📄",
    layout="wide"
)

def main():
    st.title("📄 Scanned PDF to Text Converter")
    st.markdown("Extract text from image-based PDFs (up to 30 pages)")
    
    with st.expander("📌 Before Uploading"):
        st.write("""
        - Max 30 pages per PDF
        - Supported formats: PDF
        - Text-heavy documents work best
        - Processing time: ~1 min/page
        """)
    
    uploaded_file = st.file_uploader(
        "Upload your scanned PDF",
        type=["pdf"],
        accept_multiple_files=False
    )
    
    if uploaded_file:
        # File size check
        file_size = uploaded_file.size / (1024 * 1024)  # MB
        if file_size > MAX_FILE_SIZE:
            st.error(f"File size exceeds {MAX_FILE_SIZE}MB limit")
            return
        
        # Save uploaded file
        file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Processing
        with st.status("Processing PDF...", expanded=True) as status:
            try:
                st.write("🚀 Starting text extraction...")
                start_time = time.time()
                
                progress_bar = st.progress(0)
                result_text = process_pdf(file_path)
                
                # Generate output file
                output_filename = f"{os.path.splitext(uploaded_file.name)[0]}_extracted.txt"
                output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result_text)
                
                processing_time = time.time() - start_time
                progress_bar.progress(100)
                
                status.update(
                    label="✅ Processing Complete!",
                    state="complete", 
                    expanded=False
                )
                
                # Show results
                st.success(f"Processed {uploaded_file.name} in {processing_time:.2f} seconds")
                
                # Download button
                with open(output_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="📥 Download Extracted Text",
                        data=f,
                        file_name=output_filename,
                        mime="text/plain"
                    )
                
                # Preview
                with st.expander("👀 Preview Extracted Text"):
                    st.text(result_text[:2000] + "...")  # First 2000 chars
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.stop()

if __name__ == "__main__":
    main()