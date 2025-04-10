import os
from dotenv import load_dotenv
import openai
from pinecone import Pinecone

# api keys from environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("duke-chatbot")

# embed user query and search Pinecone index
def search_duke(query: str, top_k: int = 3):
    response = openai.embeddings.create(
        input=query,
        model="text-embedding-ada-002"
    )
    query_vector = response.data[0].embedding

    search_response = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )
    return search_response

def main():
    # for testing purposes
    query = input("Enter your search query for Duke: ")
    results = search_duke(query)

    print("\nResults:")
    if results.get("matches"):
        for match in results["matches"]:
            print(f"\nID: {match['id']} | Score: {match['score']:.3f}")
            print(f"Content snippet:\n{match['metadata']['text']}\n{'-'*40}")
    else:
        print("No matches found.")

if __name__ == "__main__":
    main()
