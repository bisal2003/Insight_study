import streamlit as st
import os
import time
import google.generativeai as genai
from pdf_processor2 import process_pdf
import re

# Configuration
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
MAX_FILE_SIZE = 200  # MB
GEMINI_API_KEY = "AIzaSyDMCXugVyrMIFP4KH1DJ56uBE6wMDWODgc"
MAX_CHUNK_SIZE = 7000  # Reduced chunk size for better processing
QUESTIONS_PER_CHUNK = 3  # Reduced questions per chunk

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

st.set_page_config(
    page_title="Complete Exam Paper Converter",
    page_icon="📝",
    layout="wide"
)

def refine_extracted_text(raw_text):
    """Clean and structure the raw extracted text with better error handling"""
    chunks = [raw_text[i:i+MAX_CHUNK_SIZE] for i in range(0, len(raw_text), MAX_CHUNK_SIZE)]
    refined_text = []
    
    for i, chunk in enumerate(chunks):
        prompt = f"""
        Refine this exam paper text while maintaining:
        1. All questions and numbering exactly
        2. Complete mathematical notation
        3. Original structure
        4. Remove headers/footers
        
        Return ONLY cleaned text:
        {chunk}
        """
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 8000,
                    "temperature": 0.1
                }
            )
            refined_text.append(response.text)
            time.sleep(1.5)  # Increased delay
        except Exception as e:
            st.warning(f"Refinement error in chunk {i+1}: {str(e)}")
            refined_text.append(chunk)  # Fallback to original
    
    return "\n".join(refined_text)

def split_into_question_chunks(text):
    """Improved question splitting with better pattern matching"""
    # Enhanced pattern to catch different question formats
    question_pattern = r'(?:\d+[\.\)][^\n]+(?:\n\s*[a-z][\.\)].+)*|\d+\..+?(?=\n\d+\.|\Z))'
    questions = re.findall(question_pattern, text, re.DOTALL)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for question in questions:
        question = question.strip()
        if not question:
            continue
            
        if current_length + len(question) > MAX_CHUNK_SIZE and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_length = 0
            
        current_chunk.append(question)
        current_length += len(question)
        
        if len(current_chunk) >= QUESTIONS_PER_CHUNK:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_length = 0
    
    if current_chunk:
        chunks.append("\n".join(current_chunk))
    
    return chunks

def process_question_chunk(chunk_text, section_title=""):
    """Enhanced question processing with better error handling"""
    prompt = f"""
    Convert ALL questions to HTML with COMPLETE solutions using this EXACT structure:

    <div class="question">
        <p><strong>[Full Question]</strong></p>
        <button class="toggle-btn">Show Solution</button>
        <div class="answer" style="display:none;">
            <div class="solution-steps">
                <p><strong>Detailed Solution:</strong></p>
                <ol>
                    <li>[Step-by-step explanation]</li>
                    <li>[All calculations]</li>
                    <li>[Final answer]</li>
                </ol>
                <p><strong>Final Answer:</strong> [Complete answer]</p>
            </div>
        </div>
    </div>

    STRICT REQUIREMENTS:
    1. Process EVERY question completely
    2. Include ALL sub-parts (a, b, c etc.)
    3. Show ALL mathematical working
    4. Never skip any questions
    5. Never say "question is incomplete"
    6. If formula is given, derive the solution
    7. For numericals, show complete calculations
    8. For theory, provide detailed explanation
    9. Section: {section_title}

    QUESTIONS:
    {chunk_text}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 8000,
                "temperature": 0.3
            }
        )
        
        # Enhanced verification
        input_questions = len(re.findall(r'\d+[\.\)]', chunk_text))
        output_questions = response.text.count('class="question"')
        
        if output_questions < input_questions:
            raise ValueError(f"Only {output_questions}/{input_questions} questions processed")
            
        return response.text
        
    except Exception as e:
        error_msg = f"""
        <div class="error">
            <h3>Processing Error</h3>
            <p>{str(e)}</p>
            <div class="original-questions">
                <h4>Original Questions:</h4>
                <pre>{chunk_text[:2000]}</pre>
            </div>
        </div>
        """
        st.error(f"Chunk processing failed: {str(e)}")
        return error_msg

def convert_full_paper(raw_text):
    """Complete conversion process with better error handling"""
    with st.status("Processing document...", expanded=True) as status:
        # Stage 1: Text refinement
        status.write("🧹 Cleaning and structuring raw text...")
        refined_text = refine_extracted_text(raw_text)
        
        # Save refined text
        refined_path = os.path.join(OUTPUT_FOLDER, "refined_text.txt")
        with open(refined_path, "w", encoding="utf-8") as f:
            f.write(refined_text)
        
        # Stage 2: Split into question chunks
        status.write("✂️ Splitting into question chunks...")
        chunks = split_into_question_chunks(refined_text)
        
        # Stage 3: Process each chunk
        html_parts = [
            """<div class="container">""",
            """<h1>Exam Paper Solutions</h1>""",
            """<style>
                .question { margin-bottom: 25px; border-left: 4px solid #4CAF50; padding: 10px 15px; }
                .toggle-btn { background: #4CAF50; color: white; border: none; padding: 8px 15px; cursor: pointer; border-radius: 4px; }
                .solution-steps { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; }
                .answer { margin-top: 15px; }
                .error { color: #d32f2f; background: #ffebee; padding: 15px; border-radius: 5px; }
                pre { white-space: pre-wrap; background: #f5f5f5; padding: 10px; }
            </style>"""
        ]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        total_questions = 0
        
        for i, chunk in enumerate(chunks):
            progress = (i + 1) / len(chunks)
            progress_bar.progress(progress)
            status_text.text(f"🔧 Processing chunk {i+1}/{len(chunks)} ({(progress*100):.0f}%)...")
            
            chunk_html = process_question_chunk(chunk)
            html_parts.append(chunk_html)
            
            total_questions += chunk_html.count('class="question"')
            time.sleep(2)  # Increased delay between chunks
        
        # Final HTML
        html_parts.extend([
            "</div>",
            """
            <script>
            document.querySelectorAll('.toggle-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const answer = this.nextElementSibling;
                    answer.style.display = answer.style.display === 'none' ? 'block' : 'none';
                    this.textContent = answer.style.display === 'none' ? 'Show Solution' : 'Hide Solution';
                });
            });
            </script>
            """
        ])
        
        full_html = "\n".join(html_parts)
        
        # Final verification
        original_questions = len(re.findall(r'\d+[\.\)]', refined_text))
        processed_questions = full_html.count('class="question"')
        
        if processed_questions < original_questions:
            st.warning(f"Processed {processed_questions}/{original_questions} questions")
        else:
            st.success(f"Processed all {processed_questions} questions successfully")
        
        progress_bar.progress(1.0)
        status.update(label="✅ Conversion Complete!", state="complete", expanded=False)
        
        return full_html, refined_text

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
    
    st.title("📝 Complete Exam Paper Converter")
    st.markdown("""
    Convert PDF question papers to interactive HTML with:
    - **Complete solutions** for every question
    - **Step-by-step explanations**
    - **All sub-parts** included
    - **Mathematical working** shown
    """)
    
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
            
            # Full conversion
            html_output, refined_text = convert_full_paper(raw_text)
            
            # Save output
            output_filename = f"{os.path.splitext(uploaded_file.name)[0]}_solutions.html"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_output)
            
            # Display results
            tab1, tab2 = st.tabs(["Interactive Preview", "Raw HTML"])
            
            with tab1:
                st.components.v1.html(html_output, height=800, scrolling=True)
            
            with tab2:
                st.code(html_output, language="html")
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "💾 Download Full Solutions",
                    data=html_output,
                    file_name=output_filename,
                    mime="text/html"
                )
            with col2:
                st.download_button(
                    "📥 Download Refined Text",
                    data=refined_text,
                    file_name="refined_questions.txt",
                    mime="text/plain"
                )
            
        except Exception as e:
            st.error(f"Processing failed: {str(e)}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

if __name__ == "__main__":
    main()