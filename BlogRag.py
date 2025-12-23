import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import openai

# --- Constants ---
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # SentenceTransformer model
OPENAI_API_KEY = "your_openai_api_key"  # Replace with your OpenAI API key

# --- Load Data ---
@st.cache
def load_blog_data():
    # Replace with the path to your processed blog data CSV file
    return pd.read_csv("blog_data.csv")

# --- Embedding Creation ---
@st.cache(allow_output_mutation=True)
def create_embeddings(blog_data):
    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = model.encode(blog_data["text"].tolist(), show_progress_bar=True)
    return embeddings

# --- FAISS Index ---
@st.cache(allow_output_mutation=True)
def create_faiss_index(embeddings):
    index = faiss.IndexFlatL2(embeddings.shape[1])  # L2 distance
    index.add(embeddings)
    return index

# --- Search Function ---
def search_blog_entries(query, index, blog_data, model):
    query_embedding = model.encode([query])[0]
    distances, indices = index.search(query_embedding.reshape(1, -1), k=5)  # Retrieve top 5 matches
    results = blog_data.iloc[indices[0]]
    return results

# --- Generative AI Function ---
def generate_response(query, retrieved_entries):
    context = "\n\n".join(retrieved_entries["text"].tolist())
    prompt = f"Answer the following query based on the context:\n\nContext:\n{context}\n\nQuery: {query}\n\nAnswer:"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=300,
        temperature=0.7,
    )
    return response["choices"][0]["text"]

# --- Streamlit App ---
st.set_page_config(page_title="Blog RAG System with Images", layout="wide")

st.title("📖 Blog RAG System with Images")
st.markdown("Ask questions about the blog and retrieve summaries and pictures!")

# Load data and embeddings
blog_data = load_blog_data()
embeddings = create_embeddings(blog_data)
faiss_index = create_faiss_index(embeddings)
embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# User Input
query = st.text_input("Enter your query (e.g., 'Tell me about the trip to Sardinia')")

if query:
    # Search and retrieve
    retrieved_entries = search_blog_entries(query, faiss_index, blog_data, embedding_model)
    
    # Generate response
    response = generate_response(query, retrieved_entries)
    
    # Display results
    st.markdown(f"### AI Response for: **{query}**")
    st.markdown(response)
    
    st.markdown("### Retrieved Blog Entries:")
    for _, row in retrieved_entries.iterrows():
        st.markdown(f"#### {row['title']}")
        for image_path in eval(row["image_paths"]):  # Convert stringified list back to list
            st.image(image_path, use_column_width=True)
        st.markdown(row["text"])
        st.markdown("---")
else:
    st.info("Enter a query to search the blog.")
