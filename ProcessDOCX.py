import os
import pandas as pd
from docx import Document
import fitz  # PyMuPDF for PDF processing
import streamlit as st

# --- Helper Functions ---
def process_docx(file):
    """
    Process a single .docx file to extract text and images.
    Returns a dictionary with title, text, and image paths.
    """
    doc = Document(file)
    title = file.name[:-5]  # Use filename (without .docx) as title
    
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

def process_pdf(file):
    """
    Process a single PDF file to extract text and images.
    Returns a dictionary with title, text, and image paths.
    """
    title = file.name[:-4]  # Use filename (without .pdf) as title
    pdf = fitz.open(stream=file.read(), filetype="pdf")
    
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

# --- Streamlit App ---
st.set_page_config(page_title="Document Processor", layout="wide")

st.title("📄 Document Processor")
st.markdown("Upload `.docx` and `.pdf` files to extract text and images, and save the data into a CSV file.")

# File uploader
uploaded_files = st.file_uploader("Drag and drop your .docx or .pdf files here", type=["docx", "pdf"], accept_multiple_files=True)

# Initialize DataFrame
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["title", "text", "image_paths"])

# Process uploaded files
if uploaded_files:
    for file in uploaded_files:
        if file.name.endswith(".docx"):
            result = process_docx(file)
        elif file.name.endswith(".pdf"):
            result = process_pdf(file)
        else:
            st.warning(f"Unsupported file type: {file.name}")
            continue
        
        st.session_state.data = pd.concat(
            [st.session_state.data, pd.DataFrame([result])], ignore_index=True
        )
    st.success(f"Processed {len(uploaded_files)} file(s) successfully!")

# Display DataFrame
if not st.session_state.data.empty:
    st.markdown("### Extracted Data")
    st.dataframe(st.session_state.data)

    # Save to CSV
    if st.button("Save to CSV"):
        st.session_state.data.to_csv("processed_blog_data.csv", index=False)
        st.success("Data saved to `processed_blog_data.csv`!")
        st.markdown("You can now use this CSV file for further processing.")

# Display Images
if not st.session_state.data.empty:
    st.markdown("### Uploaded Images")
    for _, row in st.session_state.data.iterrows():
        st.markdown(f"#### {row['title']}")
        for image_path in eval(row["image_paths"]):  # Convert stringified list back to list
            st.image(image_path, use_column_width=True)
