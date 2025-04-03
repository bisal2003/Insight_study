import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s]: %(message)s')

# Define the project structure
list_of_files = [
    # Root files
    "app.py",
    "pdf_processor.py",
    "requirements.txt",
    
    # Static assets
    "uploads/",
    "outputs/",

]

# Create directories and files
for filepath in list_of_files:
    filepath = Path(filepath)
    filedir, filename = os.path.split(filepath)
    
    # Create directory if needed
    if filedir:
        os.makedirs(filedir, exist_ok=True)
        logging.info(f"Creating directory: {filedir}")

    # Create file if it doesn't exist or is empty
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        with open(filepath, "w") as f:
            # Add default content for Python files
            if filepath.suffix == ".py":
                f.write(f"# {filename}\n")
                f.write("# Auto-generated file - update with your implementation\n\n")
            # Add basic HTML structure for index.html
            elif filename == "index.html":
                f.write("<!DOCTYPE html>\n<html>\n<head>\n<title>Chatbot</title>\n</head>\n<body>\n")
                f.write("<h1>Welcome to the Chatbot</h1>\n</body>\n</html>\n")
        logging.info(f"Creating empty file: {filepath}")

logging.info("✅ Project structure created successfully!")
