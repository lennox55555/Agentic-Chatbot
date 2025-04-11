import os
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
import time
from collections import deque

def create_valid_filename(title):
    """
    Convert title to a valid filename - lowercase, no spaces, no special characters, words separated by underscores.
    
    Inputs: 
        - title (str): the filename title
    
    Returns:
        - The cleaned filename
    """
    # Convert to lowercase
    title = title.lower()
    # Replace spaces with underscores
    title = title.replace(' ', '_')
    # Remove all special characters (keeping only alphanumeric and underscores)
    title = re.sub(r'[^a-z0-9_]', '', title)
    # Replace multiple consecutive underscores with a single one
    title = re.sub(r'_+', '_', title)
    # Remove leading/trailing underscores
    return title.strip('_')

def extract_main_content(soup):
    """
    Extract the main content from the webpage, removing navigation, ads, etc.
    
    Inputs:
        - soup (BeautifulSoup): The BeautifulSoup object containing the parsed HTML.
    
    Returns:
        - str: The main content text of the webpage.
    """
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
        script.extract()
    
    # Get text and remove extra whitespace
    text = soup.get_text(separator=' ')
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return text

def scrape_website(url):
    """
    Scrape a website and return its title, main content, and links.
    
    Inputs:
        - url (str): The URL of the website to scrape.
    
    Returns:
        - tuple: A tuple containing:
            - title (str): The title of the webpage.
            - content (str): The main content of the webpage.
            - links (list): A list of valid URLs found on the page.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # skip file URLs
        file_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', 
                          '.ppt', '.pptx', '.xls', '.xlsx', '.zip', '.mp3', '.mp4']
        if any(url.lower().endswith(ext) for ext in file_extensions):
            print(f"Skipping file URL: {url}")
            return None, None, []
        
        response = requests.get(url, headers=headers, timeout=10)

        # raise exception for 4XX/5XX responses
        response.raise_for_status()  
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # extract title
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            title = title_tag.string.strip()
        else:
            # use URL path if title not found
            parsed_url = urlparse(url)
            title = parsed_url.path.strip('/')
            if not title:
                title = parsed_url.netloc
        
        # extract content
        content = extract_main_content(soup)
        
        # get all links
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            # handle relative URLs
            if not href.startswith(('http://', 'https://')):
                full_url = urljoin(url, href)
            else:
                full_url = href
            
            # skip file URLs in links
            if any(full_url.lower().endswith(ext) for ext in file_extensions):
                continue
                
            # only keep Duke URLs, but preserve their full structure (including query params)
            parsed = urlparse(full_url)
            if 'duke.edu' in parsed.netloc:
                links.append(full_url)
        
        return title, content, links
    
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None, None, []

def get_program_name(url):
    """
    Get the program name from a URL.
    
    Inputs:
        - url (str): The URL to extract the program name from.
    
    Returns:
        - str: The extracted program name, or None if not found.
    """
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path.strip('/')
    
    if not path:
        return None
    
    path_parts = path.split('/')
    
    # extract program name from pratt and the graduate school
    if domain == 'masters.pratt.duke.edu':
        if path_parts and path_parts[0] not in ['apply', 'admissions', 'events', 'news', 'people']:
            return path_parts[0]
    elif domain == 'gradschool.duke.edu':
        if len(path_parts) >= 3 and path_parts[0] == 'academics' and 'programs' in path_parts[1]:
            return path_parts[2]
    
    return path_parts[0] if path_parts else None

def normalize_url(url):
    """
    Normalize URLs for consistent comparison by:
    1. Removing fragments (#)
    2. Handling trailing slashes consistently
    """
    # Remove fragment
    url = url.split('#')[0]
    
    # Handle trailing slash consistently
    if url.endswith('/'):
        url = url[:-1]
        
    return url

def crawl_domain(base_url, output_folder):
    """
    Crawl a domain and save content by program.
    
    Inputs:
        - base_url (str): The base URL to start crawling from.
        - output_folder (str): The folder where the scraped data will be saved.
    
    Returns:
        - dict: A dictionary mapping program names to lists of scraped pages.
    """
    # parse the base URL to get domain and path
    base_parsed = urlparse(base_url)
    domain = base_parsed.netloc
    base_path = base_parsed.path.rstrip('/')
    
    # create domain folder
    domain_folder = os.path.join(output_folder, domain.replace('.', '_'))
    if not os.path.exists(domain_folder):
        os.makedirs(domain_folder)
        print(f"Created domain folder: {domain_folder}")
    
    # track visited URLs and programs
    visited = set()
    queue = deque([base_url])
    program_urls = {}

    for root, dirs, files in os.walk(domain_folder):
        for file in files:
            if file.endswith('.txt'):
                # Read the file to get the URL
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        if first_line.startswith('URL: '):
                            url = first_line[5:].strip()
                            normalized_url = normalize_url(url)
                            visited.add(normalized_url)
                            visited.add(url)
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
    
    # first phase: Discover all URLs and organize by program
    pages_processed = 0
    
    print(f"Starting discovery of {base_url}")
    
    while queue:
        url = queue.popleft()
        normalized_url = normalize_url(url)
        
        if url in visited or normalized_url in visited:
            continue
        
        visited.add(url)
        pages_processed += 1
        
        print(f"[{pages_processed}] Processing: {url}")
        
        title, content, links = scrape_website(url)
        
        # check if this URL is valid and should be saved
        if title and content:
            # get program for this URL
            program = get_program_name(url)
            
            # add to program URLs
            if program:
                if program not in program_urls:
                    program_urls[program] = []
                program_urls[program].append((url, title, content))
            else:
                # for URLs without a clear program, put in a "general" folder
                if "general" not in program_urls:
                    program_urls["general"] = []
                program_urls["general"].append((url, title, content))
        
        # add new URLs to queue
        for link in links:
            parsed_link = urlparse(link)
            
            # only process URLs on same domain
            if parsed_link.netloc != domain:
                continue
                
            # only follow links that start with or extend the base path
            link_path = parsed_link.path
            if not link_path.startswith(base_path):
                continue
                
            # add to queue if not already visited or queued
            if link not in visited and link not in queue:
                queue.append(link)
        
        # brief delay
        time.sleep(0.2)
    
    print(f"Discovery complete. Found {sum(len(urls) for urls in program_urls.values())} pages across {len(program_urls)} programs.")
    
    # second phase: Save content by program
    for program, pages in program_urls.items():
        program_folder = os.path.join(domain_folder, program)
        
        if not os.path.exists(program_folder):
            os.makedirs(program_folder)
            print(f"Created program folder: {program_folder}")
        
        print(f"\nSaving {len(pages)} pages for program: {program}")
        
        for url, title, content in pages:
            # create filename
            filename = create_valid_filename(title)
            if len(filename) < 3:
                path = urlparse(url).path.strip('/')
                filename = create_valid_filename(path.replace('/', '_'))
            if not filename:
                filename = "index"
            
            # add extension
            if not filename.endswith('.txt'):
                filename += '.txt'
            
            # truncate if too long
            if len(filename) > 100:
                filename = filename[:100]
            
            # save to file
            file_path = os.path.join(program_folder, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n\n")
                f.write(content)
            
            print(f"Saved: {file_path}")
        
        print(f"Finished saving program: {program}")
    
    return program_urls

def main():
    # starting points
    start_urls = [
        "https://masters.pratt.duke.edu/",
        "https://gradschool.duke.edu/academics/",
        "https://admissions.duke.edu/academic-possibilities/"
    ]
    
    # output folder
    output_folder = "../data/scraped_data"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # process each starting point
    for start_url in start_urls:
        print(f"\n{'='*80}\nProcessing: {start_url}\n{'='*80}")
        crawl_domain(start_url, output_folder)
    
    print("\nAll sites have been crawled and saved to their respective folders.")

if __name__ == "__main__":
    main()