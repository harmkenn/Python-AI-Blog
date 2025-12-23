import os
import pandas as pd
from docx import Document
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

# --- Streamlit App ---
st.set_page_config(page_title="Document Processor", layout="wide")

st.title("📄 Document Processor")
st.markdown("Upload `.docx` files to extract text and images, and save the data into a CSV file.")

# File uploader
uploaded_files = st.file_uploader("Drag and drop your .docx files here", type="docx", accept_multiple_files=True)

# Initialize DataFrame
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["title", "text", "image_paths"])

# Process uploaded files
if uploaded_files:
    for file in uploaded_files:
        result = process_docx(file)
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
