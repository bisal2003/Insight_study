import streamlit as st
import os
import time
import google.generativeai as genai
from pdf_processor2 import process_pdf
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
MAX_FILE_SIZE =200  # MB
GEMINI_API_KEY = "AIzaSyDMCXugVyrMIFP4KH1DJ56uBE6wMDWODgc"

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

st.set_page_config(
    page_title="PDF to HTML Converter",
    page_icon="📄",
    layout="wide"
)

def refine_extracted_text(raw_text):
    """Clean and structure the raw extracted text using Gemini"""
    prompt = f"""
    Please refine and structure this raw text extracted from a question paper PDF:
    
    1. Correct any OCR errors in the text
    2. Separate questions clearly with proper numbering
    3. Identify and mark section headers
    4. Remove any irrelevant text or artifacts
    5. Preserve all mathematical notation
    6. Ensure complete questions with their parts
    7. Format as clean plain text with clear section breaks
    8. Maintain original numbering and order
    9. Use consistent formatting for questions and answers
    10. Ensure all text is in English and ignore any non-English text
    
    Raw extracted text:
    {raw_text[:40000]}  # Process in chunks if needed
    
    Return ONLY the cleaned and structured text, no additional commentary.
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 8000,
                "temperature": 0.1
            }
        )
        return response.text
    except Exception as e:
        st.error(f"Text refinement failed: {str(e)}")
        return raw_text  # Fallback to original text

def extract_sections(refined_text):
    """Identify and extract document sections with questions from refined text"""
    sections = []
    current_section = {"title": "General Questions", "content": []}
    
    # Enhanced section detection patterns
    section_patterns = [
        r'(?:Section|Part|Set)\s*[A-Za-z0-9]+[.:]?\s*(.*)',
        r'[A-Z]{3,}\s*[.:-]\s*(.*)',
        r'\b(?:Questions?|Problems?)\b\s*(?:for|from|in)?\s*(.*)'
    ]
    
    lines = refined_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        section_found = False
        for pattern in section_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {
                    "title": line,
                    "content": []
                }
                section_found = True
                break
                
        if not section_found and current_section:
            if line.strip():
                current_section["content"].append(line)
    
    if current_section["content"]:
        sections.append(current_section)
        
    return sections

def process_section_with_retry(section, max_retries=3):
    """Process a refined section with retry logic for reliability"""
    prompt_template = """
    Convert ALL questions in this section to HTML with EXACT structure:

    <div class="question">
        <p><strong>[Q.No]. [Full Question]</strong></p>
        <button class="toggle-btn">Show Answer</button>
        <div class="answer" style="display:none;">
            <div class="solution-steps">
                <p><strong>Solution:</strong></p>
                <ol>
                    <li>[Step 1]</li>
                    <li>[Step 2]</li>
                </ol>
            </div>
            <p><strong>Answer:</strong> [Final answer]</p>
        </div>
    </div>

    REQUIREMENTS:
    1. Process ALL questions in order
    2. Preserve original numbering
    3. Detailed step-by-step solutions
    4. Use EXACT HTML structure above
    5. Section: {section_title}
    6. No need to write extra stuff like time taken, instructions etc.
    7. Do not combine or reorder questions
    8. Be precise with your content like a human expert in the field 
    9. Process only the English text, ignore any other language for better understanding
    10. Do not include any extra text or comments
    11. Do not include any extra lines or spaces
    12. Do not include any extra HTML tags or attributes
    13. Ensure understand the question properly and completely and then provide a detailed solution
    14. No extra text or comments
    15. Complete all questions and sub-questions
    16. Use your own analysis and understanding to provide the best possible solution

    CONTENT:
    {content}
    """
    
    content = "\n".join(section["content"])[:15000]  # Conservative chunk size
    prompt = prompt_template.format(
        section_title=section["title"],
        content=content
    )
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 8000,
                    "temperature": 0.2
                }
            )
            if response.text:
                return response.text
        except Exception as e:
            if attempt == max_retries - 1:
                return f"<div class='error'>Failed to process section after {max_retries} attempts: {str(e)}</div>"
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return ""

def convert_full_paper(raw_text):
    """Two-stage conversion process with progress tracking"""
    with st.status("Refining extracted text...", expanded=True) as status:
        # Stage 1: Text refinement
        status.write("🧹 Cleaning and structuring raw text...")
        refined_text = refine_extracted_text(raw_text)
        
        # Stage 2: Section processing
        sections = extract_sections(refined_text)
        if not sections:
            sections = [{"title": "Questions", "content": refined_text.split('\n')}]
        
        html_parts = [
            """<div class="container">""",
            """<h1>Exam Paper Solutions</h1>"""
        ]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Process sections sequentially
        for i, section in enumerate(sections):
            status_text.text(f"📝 Converting {section['title']}...")
            progress_bar.progress((i + 1) / (len(sections) + 1))
            
            html_parts.append(f"""
            <section id="section-{i+1}">
                <h2>{section['title']}</h2>
                {process_section_with_retry(section)}
            </section>
            """)
        
        # Finalize HTML
        html_parts.extend([
            "</div>",
            """
            <script>
            document.querySelectorAll('.toggle-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const answer = this.nextElementSibling;
                    answer.style.display = answer.style.display === 'none' ? 'block' : 'none';
                    this.textContent = answer.style.display === 'none' ? 'Show Answer' : 'Hide Answer';
                });
            });
            </script>
            """
        ])
        
        progress_bar.progress(1.0)
        status_text.text("✅ Conversion complete!")
        status.update(label="Processing Complete!", state="complete", expanded=False)
        
        return "\n".join(html_parts)

def main():
    # Clear old files
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                st.warning(f"Couldn't clear {file_path}: {e}")
    
    st.title("📄 Smart Paper Converter")
    st.markdown("Two-stage conversion: Clean → HTML")
    
    uploaded_file = st.file_uploader(
        "Upload Question Paper PDF",
        type=["pdf"],
        accept_multiple_files=False
    )
    
    if uploaded_file:
        # File validation
        file_size = uploaded_file.size / (1024 * 1024)
        if file_size > MAX_FILE_SIZE:
            st.error(f"File size exceeds {MAX_FILE_SIZE}MB limit")
            return
        
        try:
            # Save file
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Process document
            st.write("📖 Extracting text from PDF...")
            raw_text = process_pdf(file_path)
            
            # Two-stage conversion
            html_output = convert_full_paper(raw_text)
            
            # Save output
            output_filename = f"{os.path.splitext(uploaded_file.name)[0]}.html"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_output)
            
            # Results
            question_count = html_output.count('class="question"')
            st.success(f"Converted {question_count} questions")
            
            # Output options
            tab1, tab2 = st.tabs(["Preview", "Raw HTML"])
            
            with tab1:
                st.components.v1.html(html_output, height=600, scrolling=True)
            
            with tab2:
                st.code(html_output, language="html")
            
            st.download_button(
                "💾 Download Full HTML",
                data=html_output,
                file_name=output_filename,
                mime="text/html"
            )
            
        except Exception as e:
            st.error(f"Processing failed: {str(e)}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

if __name__ == "__main__":
    main()