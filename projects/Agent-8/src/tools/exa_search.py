import os
from exa_py import Exa
from langsmith import traceable
from src.tools.api_wrapper import reliable_news_tool
from config import EXA_RECENCY_DAYS, NEWS_DOMAINS, SOCIAL_DOMAINS

class ExaSearch:
    def __init__(self):
        self.api_key = os.getenv("EXA_API_KEY")
        if not self.api_key:
            raise ValueError("EXA_API_KEY environment variable is not set")
        self.client = Exa(api_key=self.api_key)

    def _published_since(self) -> str | None:
        if EXA_RECENCY_DAYS is None:
            return None
        import datetime

        d = datetime.datetime.now() - datetime.timedelta(days=int(EXA_RECENCY_DAYS))
        return d.strftime("%Y-%m-%d")

    @traceable(name="Exa.ai Formal News Search")
    def _search_formal_news(self, query: str, published_since: str | None, num_results: int, domains: list) -> list:
        formatted_results = []
        for domain in domains:
            try:
                opts = {
                    "type": "neural",
                    "category": "news",
                    "include_domains": [domain],
                    "num_results": num_results,
                }
                if published_since:
                    opts["start_published_date"] = published_since
                news_result = self.client.search(query, **opts)
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

    @traceable(name="Exa.ai Twitter/X Search")
    def _search_social_media(self, query: str, published_since: str | None, num_results: int, domains: list) -> list:
        formatted_results = []
        for domain in domains:
            try:
                # exa_py only allows category in:
                # company | research paper | news | pdf | personal site | financial report | people
                # There is no "tweet" category — it always failed before.
                opts = {
                    "type": "neural",
                    "include_domains": [domain],
                    "num_results": num_results,
                }
                if published_since:
                    opts["start_published_date"] = published_since
                social_result = self.client.search(query, **opts)
                for item in getattr(social_result, "results", []):
                    formatted_results.append({
                        "title": getattr(item, "title", "Unknown Title"),
                        "source": f"Exa.ai ({domain})",
                        "url": getattr(item, "url", ""),
                        "content": getattr(item, "text", ""),
                        "timestamp": getattr(item, "published_date", "")
                    })
            except Exception as e:
                print(f"Warning: Exa Social search failed for domain {domain}: {e}")
        return formatted_results

    @traceable(name="Exa.ai Master Search Controller")
    @reliable_news_tool(max_retries=3, timeout_seconds=30)
    def search_news(self, query: str, num_results: int = 5):
        published_since = self._published_since()

        formatted_results = []
        
        # 1. Search Formal News Domains
        formatted_results.extend(self._search_formal_news(query, published_since, num_results, NEWS_DOMAINS))

        # 2. Search Social Media Domains (X.com)
        formatted_results.extend(self._search_social_media(query, published_since, num_results, SOCIAL_DOMAINS))
            
        return formatted_results
