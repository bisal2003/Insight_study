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
MAX_FILE_SIZE = 200  # MB
GEMINI_API_KEY = "AIzaSyDMCXugVyrMIFP4KH1DJ56uBE6wMDWODgc"
MAX_SECTION_LENGTH = 10000  # Characters per section chunk
MAX_QUESTIONS_PER_CHUNK = 10  # Process questions in batches

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
    
    Requirements:
    1. Correct any OCR errors
    2. Maintain original section structure
    3. Preserve all question numbers
    4. Keep complete questions with sub-parts
    5. Remove page numbers, headers, footers
    6. Format clearly with section headers
    7. Preserve mathematical notation
    8. Ensure all text is in English
    
    Important:
    - DO NOT omit any sections or questions
    - Maintain original order exactly
    - Include ALL content between section headers
    
    Raw extracted text:
    {raw_text[:40000]}
    
    Return ONLY the cleaned text with:
    - Clear section headers
    - Numbered questions
    - Complete question text
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
        return raw_text

def extract_sections(refined_text):
    """Identify and extract document sections with questions from refined text"""
    sections = []
    current_section = {"title": "General Questions", "content": []}
    
    # Enhanced section detection with line context
    section_patterns = [
        r'(?:Section|Part|Set)\s*[A-Za-z0-9]+[.:]?\s*(.*)',
        r'[A-Z]{3,}\s*[.:-]\s*(.*)',
        r'\b(?:Questions?|Problems?)\b\s*(?:for|from|in)?\s*(.*)'
    ]
    
    lines = refined_text.split('\n')
    for i, line in enumerate(lines):
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
                    "content": [],
                    "start_line": i
                }
                section_found = True
                break
                
        if not section_found and current_section:
            if line.strip():
                current_section["content"].append(line)
    
    if current_section["content"]:
        sections.append(current_section)
        
    # Verification - ensure no content was lost
    total_lines = sum(len(s["content"]) for s in sections)
    if total_lines < len([l for l in lines if l.strip()]):
        st.warning("Some content may have been lost during section splitting")
        
    return sections

def split_large_section(section):
    """Split a large section into smaller chunks based on question count"""
    chunks = []
    current_chunk = []
    question_count = 0
    
    for line in section["content"]:
        current_chunk.append(line)
        # Detect question starts (numbers followed by . or ) )
        if re.match(r'^\d+[\.\)]', line.strip()):
            question_count += 1
            if question_count >= MAX_QUESTIONS_PER_CHUNK:
                chunks.append({
                    "title": f"{section['title']} (Part {len(chunks)+1})",
                    "content": current_chunk
                })
                current_chunk = []
                question_count = 0
    
    if current_chunk:
        chunks.append({
            "title": f"{section['title']} (Part {len(chunks)+1})" if chunks else section["title"],
            "content": current_chunk
        })
    
    return chunks

def process_question_chunk(chunk_text, section_title, chunk_num=None):
    """Process a chunk of questions with strict requirements"""
    part_label = f" (Part {chunk_num})" if chunk_num else ""
    prompt = f"""
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
    3. Include ALL sub-questions
    4. Detailed step-by-step solutions
    5. Use EXACT HTML structure above
    6. Section: {section_title}{part_label}
    7. No omissions - include everything
    8. Complete all parts of each question
    9. Do not include any commentary about truncation
    10. Process only the questions provided

    CONTENT:
    {chunk_text}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 8000,
                "temperature": 0.2
            }
        )
        return response.text
    except Exception as e:
        return f"<div class='error'>Failed to process chunk: {str(e)}</div>"

def process_section(section):
    """Process a section, splitting into chunks if needed"""
    section_content = "\n".join(section["content"])
    
    # Check if section needs splitting
    if len(section_content) > MAX_SECTION_LENGTH:
        chunks = split_large_section(section)
        if len(chunks) > 1:
            st.info(f"Splitting large section '{section['title']}' into {len(chunks)} parts")
            
            results = []
            for i, chunk in enumerate(chunks):
                chunk_text = "\n".join(chunk["content"])
                result = process_question_chunk(chunk_text, section["title"], i+1)
                results.append(result)
                time.sleep(1)  # Rate limiting
            return "\n".join(results)
    
    # Process as single chunk if not too large
    return process_question_chunk(section_content, section["title"])

def convert_full_paper(raw_text):
    """Two-stage conversion process with progress tracking"""
    with st.status("Processing document...", expanded=True) as status:
        # Stage 1: Text refinement
        status.write("🧹 Cleaning and structuring raw text...")
        refined_text = refine_extracted_text(raw_text)
        
        # Save refined text for verification
        refined_path = os.path.join(OUTPUT_FOLDER, "refined_text.txt")
        with open(refined_path, "w", encoding="utf-8") as f:
            f.write(refined_text)
        
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
        total_questions = 0
        
        # Process sections sequentially
        for i, section in enumerate(sections):
            status_text.text(f"📝 Converting {section['title']} ({i+1}/{len(sections)})...")
            progress_bar.progress((i + 1) / (len(sections) + 1))
            
            section_html = process_section(section)
            html_parts.append(f"""
            <section id="section-{i+1}">
                <h2>{section['title']}</h2>
                {section_html}
            </section>
            """)
            
            # Update question count
            total_questions += section_html.count('class="question"')
        
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
        status_text.text(f"✅ Conversion complete! Processed {total_questions} questions")
        status.update(label="Processing Complete!", state="complete", expanded=False)
        
        return "\n".join(html_parts), refined_path

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
    st.markdown("Convert PDF question papers to interactive HTML with solutions")
    
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
            html_output, refined_path = convert_full_paper(raw_text)
            
            # Save output
            output_filename = f"{os.path.splitext(uploaded_file.name)[0]}.html"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_output)
            
            # Results
            question_count = html_output.count('class="question"')
            st.success(f"Converted {question_count} questions")
            
            # Output options
            tab1, tab2, tab3 = st.tabs(["Preview", "Raw HTML", "Refined Text"])
            
            with tab1:
                st.components.v1.html(html_output, height=600, scrolling=True)
            
            with tab2:
                st.code(html_output, language="html")
            
            with tab3:
                with open(refined_path, "r", encoding="utf-8") as f:
                    refined_content = f.read()
                st.text_area("Refined Text", refined_content, height=400)
                st.download_button(
                    "📥 Download Refined Text",
                    data=refined_content,
                    file_name="refined_text.txt",
                    mime="text/plain"
                )
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "💾 Download Full HTML",
                    data=html_output,
                    file_name=output_filename,
                    mime="text/html"
                )
            with col2:
                with open(refined_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        "📥 Download Refined Text",
                        data=f,
                        file_name="refined_text.txt",
                        mime="text/plain"
                    )
            
        except Exception as e:
            st.error(f"Processing failed: {str(e)}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

if __name__ == "__main__":
    main()