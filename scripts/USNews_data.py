import os
from dotenv import load_dotenv
from pinecone import Pinecone
import openai
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# api keys from environment variables
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("duke-chatbot")

# helper function to chunk the text
def chunk_text(text, max_tokens=500):
    words = text.split()
    for i in range(0, len(words), max_tokens):
        yield ' '.join(words[i:i + max_tokens])

# scraping visible text from USNews Duke page
def scrape_usnews_text():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto("https://www.usnews.com/best-colleges/duke-university-2920", timeout=60000)
            page.wait_for_timeout(5000)
            text = page.inner_text("body")
        except PlaywrightTimeout:
            text = ""
        finally:
            browser.close()

        return text

# Embed and upsert chunks into Pinecone
def embed_and_upsert(text):
    for i, chunk in enumerate(chunk_text(text)):
        response = client.embeddings.create(
            input=chunk,
            model="text-embedding-ada-002"
        )
        vector = response.data[0].embedding

        index.upsert(
            vectors=[{
                "id": f"duke-usnews-{i}",
                "values": vector,
                "metadata": {
                    "text": chunk,
                    "source": "usnews"
                }
            }]
        )

if __name__ == "__main__":
    usnews_text = scrape_usnews_text()
    embed_and_upsert(usnews_text)
