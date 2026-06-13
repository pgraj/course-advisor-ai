import os
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

def run_test():
    # ...all the existing code, indented...
    env_path = Path.cwd() / ".env"
    print("Looking for .env at:", env_path)
    print(".env file exists?  :", env_path.exists())
    load_dotenv(env_path, override=True)

    # Load environment variables from .env file
    #load_dotenv()

    # Retrieve variables
    api_key = os.getenv("AZURE_OPENAI_KEY")
    base_url = os.getenv("AZURE_OPENAI_ENDPOINT")

    print("--- Initializing Client ---")
    print(f"Base URL: {base_url}")
    # Initialize the single OpenAI client
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    # 1. Test Chat Completion
    print("\n--- Testing Chat Completion ---")
    try:
        chat_response = client.chat.completions.create(
            model= os.getenv("CHAT_DEPLOYMENT"),
            messages=[
                {"role": "user", "content": "Hello! Reply with 'Connection successful!' if you can hear me."}
            ]
        )
        reply_text = chat_response.choices[0].message.content
        print(f"Reply: {reply_text}")
    except Exception as e:
        print(f"Chat completion failed: {e}")

    # 2. Test Embeddings
    print("\n--- Testing Embeddings ---")
    try:
        embedding_response = client.embeddings.create(
            model= os.getenv("EMBED_DEPLOYMENT"), # Change to your specific embedding model/deployment name
            input="Testing connection strength."
        )
        embedding_vector = embedding_response.data[0].embedding
        print(f"Embedding length: {len(embedding_vector)}")
    except Exception as e:
        print(f"Embedding creation failed: {e}")

if __name__ == "__main__":
    run_test()