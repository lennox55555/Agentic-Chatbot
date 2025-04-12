import os
import wikipediaapi

def sanitize_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in name).replace(" ", "_")

def main():
    # Directory for scraped data
    base_dir = os.path.join("..", "data", "scraped_data", "wikipedia_duke")
    os.makedirs(base_dir, exist_ok=True)
    
    # Set up Wikipedia API with a proper user agent
    wiki_wiki = wikipediaapi.Wikipedia(
        language='en',
        user_agent='DukeAgenticChatbot/1.0 (jfw28@duke.edu)'
    )
    
    # Retrieve the Duke University page
    page = wiki_wiki.page("Duke University")
    if not page.exists():
        print("The page 'Duke University' does not exist on Wikipedia!")
        return

    # Create a file name using the page title
    filename = sanitize_filename(page.title) + ".txt"
    filepath = os.path.join(base_dir, filename)
    
    # Save the page URL and the full text to the file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"URL: {page.fullurl}\n\n")
        f.write(page.text)
    
    print(f"Scraped Wikipedia data saved to: {filepath}")

if __name__ == "__main__":
    main()
