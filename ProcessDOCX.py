import os
import pandas as pd
from docx import Document
import fitz  # PyMuPDF for PDF processing
import streamlit as st
from github import Github  # PyGithub for GitHub API

# --- GitHub Configuration ---
GITHUB_TOKEN = "your_github_personal_access_token"  # Replace with your GitHub token
REPO_NAME = "your_github_username/your_repository_name"  # Replace with your repo name
DOCUMENTS_FOLDER = "documents"  # Folder in the repo containing the documents
OUTPUT_CSV = "processed_blog_data.csv"  # Name of the output CSV file

# --- Helper Functions ---
def process_docx(file_path):
    """
    Process a single .docx file to extract text and images.
    Returns a dictionary with title, text, and image paths.
    """
    doc = Document(file_path)
    title = os.path.basename(file_path)[:-5]  # Use filename (without .docx) as title
    
    # Extract text
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
    
    # Extract images
    image_paths = []
    for i, rel in enumerate(doc.part.rels.values()):
        if "image" in rel.target_ref:
            image_data = rel.target_part.blob
            image_filename = f"{title}_image_{i}.png"
            image_path = os.path.join("uploaded_images", image_filename)
            
            # Save image to disk
            os.makedirs("uploaded_images", exist_ok=True)
            with open(image_path, "wb") as img_file:
                img_file.write(image_data)
            
            image_paths.append(image_path)
    
    return {"title": title, "text": text, "image_paths": image_paths}

def process_pdf(file_path):
    """
    Process a single PDF file to extract text and images.
    Returns a dictionary with title, text, and image paths.
    """
    title = os.path.basename(file_path)[:-4]  # Use filename (without .pdf) as title
    pdf = fitz.open(file_path)
    
    # Extract text
    text = ""
    for page in pdf:
        text += page.get_text()
    
    # Extract images
    image_paths = []
    for i, page in enumerate(pdf):
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = pdf.extract_image(xref)
            image_data = base_image["image"]
            image_filename = f"{title}_page_{i}_image_{img_index}.png"
            image_path = os.path.join("uploaded_images", image_filename)
            
            # Save image to disk
            os.makedirs("uploaded_images", exist_ok=True)
            with open(image_path, "wb") as img_file:
                img_file.write(image_data)
            
            image_paths.append(image_path)
    
    return {"title": title, "text": text, "image_paths": image_paths}

def process_documents(folder_path):
    """
    Process all .docx and .pdf files in a folder.
    Returns a DataFrame with the extracted data.
    """
    data = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename.endswith(".docx"):
            result = process_docx(file_path)
        elif filename.endswith(".pdf"):
            result = process_pdf(file_path)
        else:
            continue
        data.append(result)
    return pd.DataFrame(data)

def push_to_github(repo_name, file_path, commit_message, token):
    """
    Push a file to a GitHub repository.
    """
    g = Github(token)
    repo = g.get_repo(repo_name)
    with open(file_path, "r") as file:
        content = file.read()
    try:
        # Check if the file already exists
        contents = repo.get_contents(file_path)
        # Update the file
        repo.update_file(contents.path, commit_message, content, contents.sha)
    except:
        # Create a new file
        repo.create_file(file_path, commit_message, content)

# --- Streamlit App ---
st.set_page_config(page_title="Document Processor", layout="wide")

st.title("📄 Document Processor with GitHub Integration")
st.markdown("Process `.docx` and `.pdf` files from a GitHub folder and save the data back to the repository.")

# Process documents button
if st.button("Process Documents"):
    # Process all documents in the GitHub folder
    st.info("Processing documents...")
    data = process_documents(DOCUMENTS_FOLDER)
    
    # Save to CSV
    data.to_csv(OUTPUT_CSV, index=False)
    st.success(f"Processed data saved to `{OUTPUT_CSV}`.")
    
    # Push CSV to GitHub
    st.info("Pushing processed data to GitHub...")
    push_to_github(REPO_NAME, OUTPUT_CSV, "Add processed blog data", GITHUB_TOKEN)
    st.success("Processed data pushed to GitHub successfully!")

# Display processed data
if os.path.exists(OUTPUT_CSV):
    st.markdown("### Processed Data")
    processed_data = pd.read_csv(OUTPUT_CSV)
    st.dataframe(processed_data)
