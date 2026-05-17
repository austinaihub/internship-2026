import operator
from typing import Annotated, List, Optional, TypedDict

class AgentState(TypedDict):
    manual_url: Optional[str]  # Bypasses Exa search when provided
    trend_topic: Optional[str]
    trend_context: Optional[str]  # Detailed context/articles
    raw_news: Optional[List[dict]] # Specific sources used by the AI
    all_retrieved_news: Optional[List[dict]] # All raw retrieved Exa search results
    writer_prompt: Optional[str] # Evaluated prompt for the writer
    post_text: Optional[str]
    image_prompt: Optional[str]
    image_path: Optional[str]  # URL or local path
    image_feedback: Optional[str] # For image regeneration feedback
    feedback: Optional[str]     # For HITL loops
    status: str                 # e.g., "planning", "approving_prompt", "writing", "approving_text", "generating_image", "approving_image", "publishing", "done"
