from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.tools.exa_search import ExaSearch
from src.tools.crawl4ai_scraper import Crawl4AIScraper
from src.state import AgentState
from pydantic import BaseModel, Field
from typing import List

class TrendAnalysis(BaseModel):
    topic: str = Field(description="A concise headline for the trend.")
    context: str = Field(description="A detailed summary of the 'who, what, when, where, why' and why it matters now.")
    used_source_urls: List[str] = Field(description="A list of the specific article URLs from the provided text that you actually used to form this trend analysis.")

import config
import random
import json
import os
from datetime import datetime

# ---------------------------------------------------------------------------
# Topic dedup — rolling window of 30 most recent topics
# ---------------------------------------------------------------------------
_USED_TOPICS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "used_topics.json")
_USED_TOPICS_PATH = os.path.normpath(_USED_TOPICS_PATH)
_MAX_HISTORY = 30

def _load_used_topics() -> list[str]:
    """Load previously used topic headlines."""
    try:
        with open(_USED_TOPICS_PATH, "r", encoding="utf-8") as f:
            entries = json.load(f)
        return [e["topic"] for e in entries]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _save_used_topic(topic: str):
    """Append topic and prune to last _MAX_HISTORY entries."""
    try:
        with open(_USED_TOPICS_PATH, "r", encoding="utf-8") as f:
            entries = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        entries = []
    entries.append({"topic": topic, "date": datetime.now().strftime("%Y-%m-%d")})
    entries = entries[-_MAX_HISTORY:]  # keep only the latest 30
    os.makedirs(os.path.dirname(_USED_TOPICS_PATH), exist_ok=True)
    with open(_USED_TOPICS_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

# ---------------------------------------------------------------------------
# Diverse query pool — balanced across 4 dimensions.
# Exa neural search works best with natural-language intent queries.
# ---------------------------------------------------------------------------
SEARCH_QUERIES = [
    # ── Law enforcement & prosecution (3) ──
    "human trafficking conviction sentencing court ruling this week",
    "cross-border trafficking ring dismantled by police operation",
    "sex trafficking or labor trafficking arrests and charges filed",

    # ── Policy & legislation (2) ──
    "new anti-trafficking law or bill passed in any country",
    "government report on human trafficking policy gaps or recommendations",

    # ── Industry & labor exploitation (3) ──
    "forced labor in agriculture construction hospitality or fishing exposed",
    "supply chain audit reveals labor exploitation or worker abuse",
    "migrant workers exploited through visa fraud or debt bondage",

    # ── Technology, prevention & survivors (4) ──
    "technology or AI tools used to detect or combat human trafficking",
    "social media platform action against trafficking or sextortion",
    "trafficking survivor story recovery support program",
    "community prevention program or awareness campaign against trafficking",
]

class TrendAnalyzer:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)

    def analyze_trends(self, state: AgentState):
        """
        Analyzes current human trafficking trends.
        """
        print("--- TREND ANALYZER: Searching for news ---")
        
        articles_content = []
        
        # 1. Primary Source: Exa
        # If user provided keywords, use them + 1 random default for broader coverage
        # Otherwise, pick 2 random queries as before
        if config.API_CONFIG.get("EXA_ENABLED", False):
            user_keywords = state.get("user_search_keywords")
            if user_keywords:
                selected_queries = [user_keywords, random.choice(SEARCH_QUERIES)]
                print(f"Using user keywords + 1 random: {selected_queries}")
            else:
                selected_queries = random.sample(SEARCH_QUERIES, k=2)
                print(f"Using 2 random queries: {selected_queries}")
            try:
                search_tool = ExaSearch()
                for query in selected_queries:
                    results = search_tool.search_news(query=query, num_results=3)
                    articles_content.extend(results)
            except Exception as e:
                print(f"Exa initialization/execution failed: {e}")
                
        if not articles_content:
            print("WARNING: Exa search failed to retrieve articles.")
            return {"status": "error", "feedback": "News gathering failed."}

        # Combine standard content and prepare raw news array
        combined_text_list = []
        raw_news_list = []
        for i, article in enumerate(articles_content):
            title = article.get("title", "")
            source = article.get("source", "")
            url = article.get("url", "")
            content = article.get("content", "")
            combined_text_list.append(f"Source: {source} ({url})\nTitle: {title}\nContent: {content[:1500]}...")
            raw_news_list.append({"title": title, "source": source, "url": url})

        combined_content = "\n\n".join(combined_text_list)

        from langchain_core.output_parsers import PydanticOutputParser
        parser = PydanticOutputParser(pydantic_object=TrendAnalysis)
        
        # Load previously used topics for dedup
        used_topics = _load_used_topics()
        dedup_instruction = ""
        if used_topics:
            topics_list = "\n".join(f"- {t}" for t in used_topics)
            dedup_instruction = f"""
            3. ALREADY COVERED (do NOT pick these topics again, choose a DIFFERENT story):
{topics_list}
            """

        # Create a prompt for the structured output
        structured_prompt = ChatPromptTemplate.from_template(
            """
            From the articles below, identify the SINGLE most newsworthy HUMAN TRAFFICKING story
            (sex trafficking, labor trafficking, debt bondage only).

            Rules:
            1. IGNORE articles about general human rights, drug trafficking, immigration, or other unrelated topics — never force a connection.
            2. If multiple trafficking stories exist, pick the one with the highest law-enforcement or legislative impact.
            {dedup_instruction}
            
            Articles:
            {articles}
            
            {format_instructions}
            """
        )
        
        chain = structured_prompt | self.llm | parser
        final_response: TrendAnalysis = chain.invoke({
            "articles": combined_content,
            "format_instructions": parser.get_format_instructions(),
            "dedup_instruction": dedup_instruction,
        })
        
        print(f"DEBUG: Trend Analysis Response: {final_response}")
        
        # Filter the raw_news_list to only include the sources the LLM specifically cited
        used_urls = final_response.used_source_urls
        filtered_news_list = [news for news in raw_news_list if news["url"] in used_urls]
        
        # Fallback in case the LLM messes up the URL formatting
        if not filtered_news_list:
            filtered_news_list = raw_news_list
        
        # Save topic to dedup history
        _save_used_topic(final_response.topic)

        return {
            "trend_topic": final_response.topic,
            "trend_context": final_response.context,
            "raw_news": filtered_news_list,
            "all_retrieved_news": raw_news_list,
            "status": "approving_trend",  # HITL: pause for user review
            "prompt_log": [{
                "agent": "trend_analyzer",
                "summary": f"Searched {len(selected_queries)} queries: {selected_queries}",
                "user_keywords": bool(user_keywords),
                "articles_found": len(articles_content),
            }],
        }
