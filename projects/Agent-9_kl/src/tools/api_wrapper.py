import functools
import time
import asyncio
from typing import Dict, Any, List
from src.tools.crawl4ai_scraper import Crawl4AIScraper

class NewsExtractionError(Exception):
    pass

def reliable_news_tool(max_retries=3, timeout_seconds=30):
    """
    A decorator to wrap news API tools with reliability standards.
    Features:
    - Retries (up to max_retries)
    - Enforces a standard output format (List of Dicts with specific keys)
    - Fallback content extraction via Crawl4AI if content is empty or missing
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    # Execute the underlying news API call with a makeshift timeout by running in executor if it's sync
                    # For simplicity, we'll assume the underlying requests library handles actual timeouts. 
                    # If dealing with complex async, we'd use asyncio.wait_for.
                    # Here we just execute the function directly.
                    results = func(*args, **kwargs)
                    
                    standardized_results = []
                    scraper = Crawl4AIScraper()
                    
                    for item in results:
                        # Extract basic fields
                        title = item.get("title", "Unknown Title")
                        source = item.get("source", "Unknown Source")
                        url = item.get("url", "")
                        content = item.get("content", "")
                        timestamp = item.get("timestamp", "")
                        score = item.get("score")

                        # Fallback Extraction Logic: If we have a URL but no substantial content
                        if url and (not content or len(content.strip()) < 50):
                            print(f"[Reliability Wrapper] Extracting full text via Crawl4AI for URL: {url}")
                            extracted = scraper.read_url(url)
                            if extracted:
                                content = extracted

                        standardized_results.append({
                            "title": title,
                            "source": source,
                            "url": url,
                            "content": content,
                            "timestamp": timestamp,
                            "score": score,
                        })
                        
                    return standardized_results

                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    last_exception = e
                    print(f"[Reliability Wrapper] Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt) # Exponential backoff
            
            print(f"[Reliability Wrapper] All {max_retries} attempts failed for {func.__name__}.")
            # Return empty list on complete failure to allow fallback tools to step in
            return []
            
        return wrapper
    return decorator
