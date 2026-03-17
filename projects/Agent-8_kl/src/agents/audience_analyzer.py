import os
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from src.state import AgentState


# ---------------------------------------------------------------------------
# Structured Output Schema
# ---------------------------------------------------------------------------

class AudienceDecision(BaseModel):
    target_audience: str = Field(description="Audience key, e.g. 'college_students', 'educators', 'business_owners', 'parents', 'lawmakers', 'general_public'.")
    audience_brief: str = Field(description="2-3 sentence writing direction for the Writer: tone, focus area, and CTA style for this audience.")
    visual_style: str = Field(description="Complete visual style brief for the Image Generator: color palette, lighting mood, setting/environment, texture, and typography style.")
    reasoning: str = Field(description="Brief explanation of why this audience was chosen.")


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are an Audience Strategist for a Human Trafficking Awareness campaign.

Given a news story and a reference table of audience profiles, you must:
1. Analyze the story content — who does it affect? what domain is it in? (legal, labor, online, etc.)
2. Match it to the SINGLE best audience from the profiles table.
3. Output a writing brief (tone + focus + CTA) tailored to that audience.
4. Output a visual style brief (color palette + lighting + setting + texture + typography) tailored to that audience.

Rules:
- Choose the audience whose trigger keywords and focus area BEST match the story content.
- If no audience is a strong match, default to "general_public".
- The audience_brief must give the Writer enough direction to adapt tone and CTA without repeating the full story.
- The visual_style must give the Image Generator enough direction to set palette, lighting, and environment without deciding the specific focal object (that is the Image Generator's job).
"""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class AudienceAnalyzer:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(AudienceDecision)
        self._profiles = self._load_profiles()

    def _load_profiles(self) -> str:
        """Load the audience profiles markdown table from config."""
        profiles_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "audience_profiles.md")
        profiles_path = os.path.normpath(profiles_path)
        try:
            with open(profiles_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"WARNING: Audience profiles not found at {profiles_path}")
            return "No audience profiles available. Default to general_public."

    @traceable(name="Audience Analysis")
    def analyze_audience(self, state: AgentState) -> dict:
        """
        Analyzes the trend content and selects the best target audience.
        Outputs audience_brief (for Writer) and visual_style (for Image Generator).
        """
        print("--- AUDIENCE ANALYZER: Matching content to target audience ---")

        topic = state.get("trend_topic")
        context = state.get("trend_context")

        if not topic or not context:
            return {
                "target_audience": "general_public",
                "audience_brief": "Write for a general audience. Use accessible language and include the national hotline number.",
                "visual_style": "Cinematic teal-and-orange color grade, dramatic chiaroscuro lighting, high-contrast bold typography, gritty urban texture.",
                "status": "audience_selected",
            }

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=(
                f"Story Topic: {topic}\n"
                f"Story Context: {context}\n\n"
                f"Audience Profiles Reference:\n{self._profiles}\n\n"
                f"Select the best audience and provide the writing brief and visual style brief."
            ))
        ]

        decision: AudienceDecision = self.llm.invoke(messages)
        print(f"--- AUDIENCE ANALYZER: Selected '{decision.target_audience}' | Reason: {decision.reasoning} ---")

        return {
            "target_audience": decision.target_audience,
            "audience_brief": decision.audience_brief,
            "visual_style": decision.visual_style,
            "status": "approving_audience",
        }
