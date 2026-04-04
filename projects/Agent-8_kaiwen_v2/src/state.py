import operator
from typing import Annotated, List, Optional, TypedDict
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # --- Pipeline Data ---
    trend_topic: Optional[str]
    trend_context: Optional[str]        # Detailed context/articles
    raw_news: Optional[List[dict]]      # Specific sources used by the AI
    all_retrieved_news: Optional[List[dict]]  # All raw retrieved Exa search results
    target_audience: Optional[str]      # e.g. "college_students", "educators"
    audience_brief: Optional[str]       # Tone/focus/CTA direction for Writer
    visual_style: Optional[str]         # Complete visual style brief for Image Generator
    visual_elements: Optional[str]      # Event-specific visual anchors from AudienceAnalyzer
    writer_prompt: Optional[str]        # Evaluated prompt for the writer
    post_text: Optional[str]
    image_prompt: Optional[str]
    image_path: Optional[str]           # URL or local path
    overlay_text: Optional[dict]        # {"headline": "...", "key_fact": "...", "source_line": "..."}
    image_feedback: Optional[str]       # For image regeneration feedback
    feedback: Optional[str]             # For HITL loops
    status: str                         # e.g., "planning", "approving_text", "done"

    # --- Supervisor Control ---
    next: Optional[str]                 # Supervisor's routing decision
    run_id: Optional[str]               # Unique ID per pipeline run
    retry_counts: Optional[dict]        # {"writer": 0, "image_generator": 0, ...}
    messages: Annotated[List[BaseMessage], operator.add]  # Inter-agent message log
