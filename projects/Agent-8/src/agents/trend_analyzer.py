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
        if config.API_CONFIG.get("EXA_ENABLED", False):
            print("Trying Exa Search as Primary Source...")
            try:
                search_tool = ExaSearch()
                # Use a much more targeted semantic query to avoid generic human rights noise
                articles_content = search_tool.search_news(query="latest human trafficking arrests, legislation, and breaking trafficking news", num_results=5)
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
        
        # Create a prompt for the structured output
        structured_prompt = ChatPromptTemplate.from_template(
            """
            You are a Trend Analyzer.
            Analyze the following news articles and identify the SINGLE most important current trend or story.
            
            CRITICAL RULES FOR ACCURACY:
            1. The trend MUST be explicitly and exclusively about HUMAN TRAFFICKING (e.g., labor trafficking, sex trafficking, debt bondage). 
            2. You MUST COMPLETELY IGNORE any articles that are about general human rights, drug trafficking, immigration, or other unrelated crimes. Do NOT force a connection or settle for a "general human rights" summary.
            3. Base your decision ONLY on the articles provided that actually meet the criteria above.
            4. If multiple relevant human trafficking stories exist, choose the one that is mentioned most frequently or carries the highest global legislative/law enforcement impact.
            
            Articles:
            {articles}
            
            {format_instructions}
            """
        )
        
        chain = structured_prompt | self.llm | parser
        final_response: TrendAnalysis = chain.invoke({
            "articles": combined_content,
            "format_instructions": parser.get_format_instructions()
        })
        
        print(f"DEBUG: Trend Analysis Response: {final_response}")
        
        # Filter the raw_news_list to only include the sources the LLM specifically cited
        used_urls = final_response.used_source_urls
        filtered_news_list = [news for news in raw_news_list if news["url"] in used_urls]
        
        # Fallback in case the LLM messes up the URL formatting
        if not filtered_news_list:
            filtered_news_list = raw_news_list
        
        return {
            "trend_topic": final_response.topic,
            "trend_context": final_response.context,
            "raw_news": filtered_news_list,
            "all_retrieved_news": raw_news_list,
            "status": "planning" # Hand back to planner
        }
