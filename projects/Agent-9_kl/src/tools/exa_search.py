import os
from exa_py import Exa
from langsmith import traceable
from src.tools.api_wrapper import reliable_news_tool
from config import NEWS_DOMAINS

class ExaSearch:
    def __init__(self):
        self.api_key = os.getenv("EXA_API_KEY")
        if not self.api_key:
            raise ValueError("EXA_API_KEY environment variable is not set")
        self.client = Exa(api_key=self.api_key)

    @traceable(name="Exa.ai Formal News Search")
    def _search_formal_news(self, query: str, last_week: str, num_results: int, domains: list) -> list:
        formatted_results = []
        for domain in domains:
            try:
                news_result = self.client.search_and_contents(
                    query,
                    type="neural",
                    category="news",
                    start_published_date=last_week,
                    include_domains=[domain],
                    num_results=num_results,
                    text=True
                )
                for item in getattr(news_result, "results", []):
                    formatted_results.append({
                        "title": getattr(item, "title", "Unknown Title"),
                        "source": f"Exa.ai ({domain})",
                        "url": getattr(item, "url", ""),
                        "content": getattr(item, "text", ""),
                        "timestamp": getattr(item, "published_date", "")
                    })
            except Exception as e:
                print(f"Warning: Exa News search failed for domain {domain}: {e}")
        return formatted_results

    @traceable(name="Exa.ai Master Search Controller")
    @reliable_news_tool(max_retries=3, timeout_seconds=30)
    def search_news(self, query: str, num_results: int = 5):
        import datetime
        last_week = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")

        formatted_results = []
        
        # Search Formal News Domains
        formatted_results.extend(self._search_formal_news(query, last_week, num_results, NEWS_DOMAINS))
            
        return formatted_results
