import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path.cwd() / ".env", override=True)

client = OpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

EMBED_DEPLOYMENT = os.getenv("EMBED_DEPLOYMENT")
CHAT_DEPLOYMENT = os.getenv("CHAT_DEPLOYMENT")

def embed_texts(texts):
    response = client.embeddings.create(model=EMBED_DEPLOYMENT, input=texts)
    return [item.embedding for item in response.data]