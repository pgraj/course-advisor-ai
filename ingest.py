import os
import chromadb
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, AzureOpenAI
from utils import client, embed_texts



# Retrieve variables
api_key = os.getenv("AZURE_OPENAI_KEY")
base_url = os.getenv("AZURE_OPENAI_ENDPOINT")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

# 2. Chunking function
def chunk_text(text, chunk_size=300, overlap=50):
    """Split text into overlapping chunks of ~chunk_size words."""
    words = text.split()
    # split into words, step through with (chunk_size - overlap) stride,
    chunks = []
    stride = chunk_size - overlap
    
    # join each window back into a string, return the list
    if len(words) <= chunk_size:
        return [" ".join(words)]
    for i in range(0, len(words),stride):
        window = words[i : i + chunk_size] 
        chunks.append(" ".join(window))
        if i + chunk_size >= len(words):
            break
    
    return chunks

# 3. Embedding function 
#def embed_texts(texts):
#    embed_model = os.getenv("EMBED_DEPLOYMENT")
#   response = client.embeddings.create(model=embed_model, input=texts)
#    return [item.embedding for item in response.data]

# 4. Main flow
def main():
    chroma_path = Path(__file__).parent / "chroma_db"
    chroma = chromadb.PersistentClient(path=str(chroma_path))
    #    - chroma = chromadb.PersistentClient(path="chroma_db")
    #    - collection = chroma.get_or_create_collection("policies")
    collection = chroma.get_or_create_collection("policies")
    policies_dir = Path(__file__).parent / "data" / "policies"

    # - for each .md file in data/policies/  (hint: Path.glob("*.md")):
    for file in policies_dir.glob("*.md"):
        filename = file.name
        with open (file, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = chunk_text(text)
        #read text → chunk it → embed the chunks (ONE call per file, pass the list)
        if not chunks or (len(chunks) == 1 and chunks[0] == ""):
            continue
        embeddings = embed_texts(chunks)
        #     ids=[f"{filename}_chunk_{i}" ...],
        
        chunk_ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]
        #   metadatas=[{"source": filename, "chunk": i} ...])
        metadatas = [{"source": filename, "chunk": i} for i in range(len(chunks))]
        #→ collection.upsert(documents=chunks, embeddings=...,
        collection.upsert(
            documents=chunks,
            embeddings=embeddings,
            ids=chunk_ids,
            metadatas=metadatas
        ) 
        #    - print per file: "filename: N chunks"
        print(f"{filename}: {len(chunks)} chunks processed.")
    #    - print final: collection.count()
    print(f"\nFinal collection count: {collection.count()} total vectors in database.")
    question = "What refund do I get if I withdraw after census?"
    q_embedding = embed_texts([question])[0]
    results = collection.query(query_embeddings=[q_embedding], n_results=2)
    print("\nVerification:", question)
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"  → {meta['source']} (chunk {meta['chunk']})")

if __name__ == "__main__":
    main()