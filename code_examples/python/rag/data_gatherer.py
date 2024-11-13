import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from urllib.parse import urljoin
from vector_database import VectorStore

class BerkshireScraper:
    """
    Scrapes shareholder letters from Berkshire Hathaway's website.
    """
    
    def __init__(self):
        """Initialize with the base URL for Berkshire's letters"""
        self.base_url = "https://www.berkshirehathaway.com/letters/"
        self.letters_page = "letters.html"
    
    def get_letter_urls(self) -> List[str]:
        """
        Scrape all shareholder letter URLs from the letters page
        
        Returns:
            List[str]: List of URLs to individual letters
        """
        
        return [f"./rag/letters/{year}.txt" for year in range(1977, 1998)]
    
    def scrape_letter(self, url: str) -> Dict[str, str]:
        """
        Scrape content from a single letter URL
        
        Args:
            url (str): URL of the letter to scrape
            
        Returns:
            Dict with letter content and metadata
        """
        try:
            # Extract year from file path (assuming format like '1982.txt')
            year_match = re.search(r'(\d{4})', url)
            year = year_match.group(1) if year_match else "Unknown"
            
            # Read the content from the local txt file
            with open(url, 'r', encoding='utf-8') as file:
                content = file.read()
            
            return {
                'year': year,
                'url': url,
                'content': content,
                'format': 'txt'
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
        
    def scrape_all_letters(self) -> List[Dict[str, str]]:
        """
        Scrape all available shareholder letters
        
        Returns:
            List[Dict]: List of dictionaries containing letter content and metadata
        """
        letters = []
        urls = self.get_letter_urls()
        
        for url in urls:
            letter = self.scrape_letter(url)
            if letter:
                letters.append(letter)
        
        # Sort by year
        letters.sort(key=lambda x: x['year'], reverse=True)
        return letters
    
if __name__ == "__main__":
    # Create scraper and get letters
    scraper = BerkshireScraper()
    letters = scraper.scrape_all_letters()

    # Print summary of what we found
    print(f"Found {len(letters)} letters:")
    # for letter in letters:
    #     print(f"Year: {letter['year']}, Format: {letter['format']}, URL: {letter['url']}")

    # Example of storing in vector database
    vector_store = VectorStore()

    # Store each letter in the vector database
    for letter in letters:
        # Chunk the content for very long letters
        max_chunk_size = 2000  # Define the maximum chunk size
        content = letter['content']
        chunks = [content[i:i + max_chunk_size] for i in range(0, len(content), max_chunk_size)]
        
        for chunk in chunks:
            vector_store.add_to_index(
                text=chunk,
                metadata={
                    'year': letter['year'],
                    'url': letter['url'],
                    'format': letter['format'],
                }
            )