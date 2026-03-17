import asyncio
from crawl4ai import *

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
        Reads the content of a URL using Crawl4AI.
        Runs the async extraction in a synchronous wrapper since the calling code is synchronous.
        """
        try:
            # Create a new event loop to ensure it can run even if called from a thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            content = loop.run_until_complete(self._crawl_async(url))
            loop.close()
            return content
        except Exception as e:
            print(f"Error reading URL with Crawl4AI: {e}")
            return ""
