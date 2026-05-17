import asyncio
from crawl4ai import *
import requests
from bs4 import BeautifulSoup

class Crawl4AIScraper:
    def __init__(self):
        # We initialize the crawler in the read_url method to handle the async context properly
        pass

    async def _crawl_async(self, url: str) -> str:
        # We need an async function to use AsyncWebCrawler
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=url,
            )
            return result.markdown

    def read_url(self, url: str) -> str:
        """
        Reads the content of a URL using Crawl4AI with a synchronous wrapper.
        Includes a standard requests fallback if the async loop crashes in Streamlit.
        """
        if not url.startswith("http"):
            url = "https://" + url
            
        try:
            # Create a new event loop to ensure it can run even if called from a thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            content = loop.run_until_complete(self._crawl_async(url))
            loop.close()
            
            if content and len(content) > 50:
                return content
        except Exception as e:
            print(f"Error reading URL with Crawl4AI: {e} | Switching to fallback...")
            
        # Fallback to standard Requests + BeautifulSoup
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = ' '.join([p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3'])])
            return text
        except Exception as fallback_err:
            print(f"Fallback request also failed: {fallback_err}")
            return "ERROR: Could not retrieve article content from the given URL."
