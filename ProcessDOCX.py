import os
import pandas as pd
from docx import Document

def extract_text_and_images(docx_folder):
    """
    Extract text and images from .docx files in a folder.
    Returns a DataFrame with columns: title, text, image_paths.
    """
    data = []
    
    for filename in os.listdir(docx_folder):
        if filename.endswith(".docx"):
            doc_path = os.path.join(docx_folder, filename)
            doc = Document(doc_path)
            
            # Extract text
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
            
            # Extract images
            image_paths = []
            for i, rel in enumerate(doc.part.rels.values()):
                if "image" in rel.target_ref:
                    image_data = rel.target_part.blob
                    image_filename = f"{filename[:-5]}_image_{i}.png"
                    image_path = os.path.join(docx_folder, "images", image_filename)
                    
                    # Save image to disk
                    os.makedirs(os.path.join(docx_folder, "images"), exist_ok=True)
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_data)
                    
                    image_paths.append(image_path)
            
            # Add to data
            data.append({
                "title": filename[:-5],  # Use filename as title
                "text": text,
                "image_paths": image_paths
            })
    
    # Convert to DataFrame
    return pd.DataFrame(data)

# Example usage
docx_folder = "path_to_docx_files"
blog_data = extract_text_and_images(docx_folder)
blog_data.to_csv("blog_data.csv", index=False)  # Save as CSV for later use
