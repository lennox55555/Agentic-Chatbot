import os
import openai
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import tiktoken

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("PINECONE_API_KEY")
ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
INDEX_NAME = os.getenv("PINECONE_INDEX", "agenticchatbotdb")
NAMESPACE = os.getenv("PINECONE_NAMESPACE", "ns1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MAX_TOKENS = 8000

pc = Pinecone(api_key=API_KEY)
client = openai.OpenAI(api_key=OPENAI_API_KEY)
tokenizer = tiktoken.get_encoding("cl100k_base")

# Check if Pinecone index exists, create if it doesn't
existing_indexes = pc.list_indexes().names()
if INDEX_NAME not in existing_indexes:
    print(f"Index '{INDEX_NAME}' not found. Creating index...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=ENVIRONMENT)
    )

index = pc.Index(INDEX_NAME)

def split_by_paragraphs(text, max_tokens=MAX_TOKENS):
    """
    Split text into chunks by paragraphs while respecting token limits.
    This preserves natural text boundaries without requiring NLTK.
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_token_count = 0
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        paragraph_tokens = tokenizer.encode(paragraph)
        tokens_count = len(paragraph_tokens)
        
        # If a single paragraph exceeds the max, we need to split it
        if tokens_count > max_tokens:
            # Process oversized paragraph with a sliding window approach
            for i in range(0, len(paragraph_tokens), max_tokens):
                window = paragraph_tokens[i:i + max_tokens]
                chunks.append(tokenizer.decode(window))
            continue
            
        # If adding this paragraph would exceed max tokens, start a new chunk
        if current_token_count + tokens_count > max_tokens:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_token_count = 0
        
        # Add paragraph to current chunk
        current_chunk.append(paragraph)
        current_token_count += tokens_count
    
    # Add the last chunk if there's anything left
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
    
    return chunks

def generate_embedding(text):
    """Generate embeddings for text content preserving all content."""
    try:
        if not text.strip():
            print("Warning: Empty text passed to generate_embedding")
            return [0.01] * 1536  # Return non-zero embedding to avoid Pinecone error
        
        # Get token count
        token_count = len(tokenizer.encode(text))
        
        # If text fits within token limit, embed it directly
        if token_count <= MAX_TOKENS:
            response = client.embeddings.create(
                input=[text],
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        
        # Otherwise, split and average embeddings
        chunks = split_by_paragraphs(text, MAX_TOKENS)
        
        if not chunks:
            print("Warning: No chunks generated")
            return [0.01] * 1536
            
        embeddings = []
        for chunk in chunks:
            if not chunk.strip():
                continue
                
            response = client.embeddings.create(
                input=[chunk],
                model="text-embedding-ada-002"
            )
            embeddings.append(response.data[0].embedding)

        # If no embeddings were generated, return a placeholder
        if not embeddings:
            print("Warning: No embeddings generated")
            return [0.01] * 1536
            
        # Average across chunks
        avg_embedding = [sum(values) / len(values) for values in zip(*embeddings)]
        
        # Ensure we don't have an all-zero embedding (causes Pinecone error)
        if all(v == 0 for v in avg_embedding):
            print("Warning: All-zero embedding detected, adding small values")
            avg_embedding = [0.01] * 1536
            
        return avg_embedding
        
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        # Return non-zero embedding to avoid Pinecone error
        return [0.01] * 1536

def main():
    # Base directory containing the data structure
    base_directory = "../data/scraped_data"
    
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
    
    print(f"Successfully uploaded {count} vectors to Pinecone index '{INDEX_NAME}'")

if __name__ == "__main__":
    main()