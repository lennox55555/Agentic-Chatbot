import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

def scrape_usnews_text():
    """
    Scrape the visible text from the Duke University USNews page
    and return the text along with the URL.
    """
    url = "https://www.usnews.com/best-colleges/duke-university-2920"
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(5000) 
            text = page.inner_text("body")
        except PlaywrightTimeout:
            print("⏰ Timeout encountered while loading the page.")
            text = ""
        finally:
            browser.close()
    return text, url

def main():
    output_dir = os.path.join("..", "data", "scraped_data", "usnews_duke")
    os.makedirs(output_dir, exist_ok=True)
    
    scraped_text, url = scrape_usnews_text()
    
    output_filepath = os.path.join(output_dir, "duke_university_usnews.txt")
    
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n\n")
        f.write(scraped_text)
    
    print(f"Scraped USNews data saved to: {output_filepath}")

if __name__ == "__main__":
    main()
