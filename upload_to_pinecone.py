import os
import pinecone
import openai
from dotenv import load_dotenv

load_dotenv()

def generate_embedding(text):
    """Generate embeddings for text content."""
    try:
        response = openai.Embedding.create(
            input=[text],
            model="text-embedding-ada-002"
        )
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return [0.0] * 1536


def main():
    # Load API keys from environment variables
    openai.api_key = os.getenv('OPENAI_API_KEY')
    pinecone_api_key = os.getenv('PINECONE_API_KEY')
    
    # Base directory containing the data structure
    base_directory = "./data"
    
    # Initialize Pinecone
    pinecone.init(api_key=pinecone_api_key)
    
    # Set index name
    index_name = "duke-programs"
    
    # Create index if it doesn't exist
    if index_name not in pinecone.list_indexes():
        pinecone.create_index(
            name=index_name,
            dimension=1536,  # OpenAI embedding dimension
            metric="cosine"
        )
    
    # Connect to index
    index = pinecone.Index(index_name)
    
    # Prepare to collect vectors
    vectors = []
    count = 0
    
    # Walk through all files
    print("Processing files...")
    for root, dirs, files in os.walk(base_directory):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                
                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Generate embedding from content
                    embedding = generate_embedding(content)
                    
                    # Create vector with filename in metadata
                    vector = {
                        'id': f"doc_{count}",
                        'values': embedding,
                        'metadata': {
                            'filename': file
                        }
                    }
                    
                    vectors.append(vector)
                    count += 1
                    
                    print(f"Processed: {file}")
                    
                    # Upload in batches of 100
                    if len(vectors) >= 100:
                        index.upsert(vectors=vectors)
                        print(f"Uploaded batch of {len(vectors)} vectors")
                        vectors = []
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
    
    # Upload any remaining vectors
    if vectors:
        index.upsert(vectors=vectors)
        print(f"Uploaded final batch of {len(vectors)} vectors")
    
    print(f"Successfully uploaded {count} vectors to Pinecone index '{index_name}'")


if __name__ == "__main__":
    main()