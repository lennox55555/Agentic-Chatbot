import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import openai
import wikipediaapi

# api keys from environment variables
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# index info and embedding size
index_name = "duke-chatbot"
dimension = 1536

# creates index in pinecone if not already made
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=dimension,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1") 
    )

index = pc.Index(index_name)

# wikipedia api
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='DukeAgenticChatbot/1.0 (jfw28@duke.edu)'
)

page = wiki_wiki.page("Duke University")

# helper function to chunk the text
def chunk_text(text, max_tokens=500):
    words = text.split()
    for i in range(0, len(words), max_tokens):
        yield ' '.join(words[i:i + max_tokens])

# Embed and upsert chunks into Pinecone
for i, chunk in enumerate(chunk_text(page.text)):
    response = client.embeddings.create(
        input=chunk,
        model="text-embedding-ada-002"
    )
    vector = response.data[0].embedding

    index.upsert(
        vectors=[{
            "id": f"duke-wiki-{i}",
            "values": vector,
            "metadata": {
                "text": chunk,
                "source": "wikipedia"
            }
        }]
    )
