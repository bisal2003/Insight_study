import streamlit as st
import os
import time
import google.generativeai as genai
from pdf_processor2 import process_pdf
import re
import tempfile
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
UPLOAD_FOLDER = tempfile.mkdtemp()
OUTPUT_FOLDER = tempfile.mkdtemp()
MAX_FILE_SIZE = 200  # MB
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # From environment variable
MAX_QUESTION_TOKENS = 4000  # Tokens per individual question
DELAY_BETWEEN_QUESTIONS = 1  # Seconds
MAX_REQUESTS_PER_MINUTE = 60  # Gemini's free tier limit

# Initialize Gemini
if not GEMINI_API_KEY:
    st.error("Gemini API key not configured. Please set GEMINI_API_KEY environment variable.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(
    page_title="Complete Question Processor",
    page_icon="📝",
    layout="wide"
)

def cleanup():
    """Clean up temporary directories"""
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        try:
            shutil.rmtree(folder, ignore_errors=True)
        except Exception as e:
            st.warning(f"Couldn't remove {folder}: {e}")

def refine_extracted_text(raw_text):
    """Clean and structure the raw extracted text"""
    prompt = f"""
    Extract and structure all questions from this exam paper text:
    1. Preserve original numbering and sub-parts (a, b, c)
    2. Keep complete mathematical notation
    3. Remove headers/footers/page numbers
    
    Return in this exact format:
    [Q.No]. [Full Question Text]
    [Sub-part a]. [Question text]
    [Sub-part b]. [Question text]
    
    Text to process:
    {raw_text[:30000]}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"max_output_tokens": 8000, "temperature": 0.1}
        )
        return response.text
    except Exception as e:
        st.error(f"Text refinement failed: {str(e)}")
        return raw_text

def extract_individual_questions(refined_text):
    """Extract each question and sub-question separately"""
    questions = []
    current_question = ""
    
    # Enhanced pattern to capture question numbers and sub-parts
    question_pattern = r'(?:\d+[a-z]?[\.\)]|\b[a-z][\.\)]).+?(?=\n\d+[a-z]?[\.\)]|\n\b[a-z][\.\)]|\Z)'
    
    matches = re.finditer(question_pattern, refined_text, re.DOTALL)
    for match in matches:
        question_text = match.group().strip()
        if question_text:
            questions.append(question_text)
    
    return questions

def process_single_question(question_text):
    """Process one question to get complete solution"""
    if not question_text.strip() or len(question_text.strip()) < 5:
        return ""
        
    prompt = f"""
    For this exam question, provide:
    1. Complete question text
    2. Detailed step-by-step solution
    3. Final answer
    4. No need css or JS just keep the class and id same
    5. No need for instruction and marking scheme
    
    Requirements:
    - Skip any commentary about incompleteness
    - Never include "```html" or code blocks
    - If question is incomplete, just return the question text without solution
    - Keep the exact HTML structure below
    
    Format exactly like this:
    <div class="question">
        <p><strong>[Full Question]</strong></p>
        <button class="toggle-btn">Show Solution</button>
        <div class="answer" style="display:none;">
            <div class="solution-steps">
                <p><strong>Solution:</strong></p>
                <ol>
                    <li>[Step 1 explanation]</li>
                    <li>[Step 2 working]</li>
                </ol>
                <p><strong>Final Answer:</strong> [Complete answer]</p>
            </div>
        </div>
    </div>

    Question to process:
    {question_text}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": MAX_QUESTION_TOKENS,
                "temperature": 0.2
            }
        )
        cleaned_output = response.text.replace("```html", "").replace("```", "").strip()
        return cleaned_output
    except genai.types.BlockedPromptException:
        return f"<div class='question'><p>⚠️ Question content blocked by safety filters</p></div>"
    except Exception as e:
        return f"<div class='error'>Error processing question: {str(e)}</div>"

def convert_full_paper(raw_text):
    """Process each question completely independently"""
    with st.status("Processing...", expanded=True) as status:
        # Stage 1: Text refinement
        status.write("🧹 Extracting questions from text...")
        refined_text = refine_extracted_text(raw_text)
        
        # Save refined text
        refined_path = os.path.join(OUTPUT_FOLDER, "refined_text.txt")
        try:
            with open(refined_path, "w", encoding="utf-8") as f:
                f.write(refined_text)
        except Exception as e:
            st.error(f"Couldn't save refined text: {str(e)}")
        
        # Stage 2: Extract individual questions
        status.write("🔍 Identifying all questions...")
        questions = extract_individual_questions(refined_text)
        
        # Stage 3: Process each question
        html_parts = []
        progress_bar = st.progress(0)
        processed_count = 0
        
        for i, question in enumerate(questions):
            if i >= MAX_REQUESTS_PER_MINUTE:
                st.warning(f"Stopped after {MAX_REQUESTS_PER_MINUTE} questions (API limit)")
                break
                
            progress = (i + 1) / min(len(questions), MAX_REQUESTS_PER_MINUTE)
            progress_bar.progress(progress)
            status.write(f"📝 Processing question {i+1}/{len(questions)}...")
            st.toast(f"Processing question {i+1}", icon="⏳")
            
            question_html = process_single_question(question)
            if question_html:
                html_parts.append(question_html)
                processed_count += 1
            time.sleep(DELAY_BETWEEN_QUESTIONS)
        
        full_html = "\n".join(html_parts)
        status.success(f"✅ Processed {processed_count} questions")
        return full_html, refined_path

def main():
    # Clear old files
    cleanup()
    
    st.title("📄 Smart Paper Converter")
    st.markdown("Convert PDF question papers to interactive HTML with solutions")
    
    # API call log section
    st.sidebar.title("API Call Transparency")
    st.sidebar.info("Below are all Gemini API calls made during processing")
    
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
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass

if __name__ == "__main__":
    main()
    cleanup()  # Final cleanup
