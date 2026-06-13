import os
import json
import chromadb
from pathlib import Path
from dotenv import load_dotenv
from utils import client, embed_texts, CHAT_DEPLOYMENT





def ask(question):
      # 1. Establish data link
    chroma_path = Path(__file__).parent / "chroma_db"
    chroma = chromadb.PersistentClient(path=str(chroma_path))
    collection = chroma.get_or_create_collection("policies")
    
    # 2. Embeds the question
    question_embedding = embed_texts([question])[0]
    
    # 3. Queries Chroma for top 3 chunks
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=3
    )
   # Safely unfold arrays
    retrieved_chunks = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    # Sends question + chunks to gpt-4.1-mini with a grounding system prompt
    sources = [meta.get("source", "Unknown") for meta in metadatas if meta]
    # Keep list elements unique but ordered
    unique_sources = list(dict.fromkeys(sources))
    # 4. Construct Grounded prompt template injection
    context_str = "\n\n".join([f"[Context {i+1}]: {text}" for i, text in enumerate(retrieved_chunks)])
    SYSTEM_PROMPT = """You are the Course Advisor for Horizon Institute of Applied Studies (HIAS).
    Answer the student's question using ONLY the context provided below.
    If the answer is not in the context, say "I don't have that information in the policy documents."
    Be concise and cite which policy the answer comes from.

    CONTEXT:
    {context}"""
    # 5. Execute text compilation
    response = client.chat.completions.create(
        model=CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(context=context_str)},
            {"role": "user", "content": question},
        ],
    )
    return {
        "answer": response.choices[0].message.content,
        "sources": unique_sources
    }
if __name__ == "__main__":
    test_questions = [
        "What refund do I get if I withdraw after census?",
        "How do I enroll?",
        "What happens if I fail an exam?"
    ]
    
    print("=== Launching Grounded QA Verification Runner ===\n")
    for q in test_questions:
        print(f"Question: \"{q}\"")
        output = ask(q)
        print(f"Answer  : {output['answer']}")
        print(f"Sources : {output['sources']}\n" + "-"*50 + "\n")