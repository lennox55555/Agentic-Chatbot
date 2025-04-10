import os
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("PINECONE_API_KEY")
ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
INDEX_NAME = os.getenv("PINECONE_INDEX", "agenticchatbotdb")
NAMESPACE = os.getenv("PINECONE_NAMESPACE", "ns1")

pc = Pinecone(api_key=API_KEY)

existing_indexes = pc.list_indexes().names()
if INDEX_NAME not in existing_indexes:
    print(f"Index '{INDEX_NAME}' not found. Creating index...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=1024,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=ENVIRONMENT)
    )

index = pc.Index(INDEX_NAME)

dummy_vector = [0.0] * 1024
dummy_vector[0] = 1.0  

response = index.upsert(
    vectors=[
        {
            "id": "test-vector",
            "values": dummy_vector,
            "metadata": {"description": "Test upload vector"}
        }
    ],
    namespace=NAMESPACE
)

print("Upsert Response:", response)
