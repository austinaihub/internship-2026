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
    visual_style: str = Field(description="Short visual direction for the Image Generator: color palette (2-3 tones), lighting mood, and overall feel. Keep it under 25 words.")
    visual_elements: str = Field(
        description=(
            "ONE single visual anchor extracted from THIS news event — the most powerful, "
            "specific image that captures the story's essence. Pick ONE concrete detail "
            "(a place, an object, a moment) not a list of multiple scenes. "
            "Example: 'a row of confiscated passports spread on a steel table'. "
            "NEVER use generic descriptions. Keep it to one sentence. "
            "ANONYMITY: If describing people, use ONLY anonymous depictions — "
            "silhouettes, hands, backs of heads. Never name real individuals."
        )
    )
    reasoning: str = Field(description="Brief explanation of why this audience was chosen.")


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are an Audience Strategist for a Human Trafficking Awareness campaign.

Given a news story and a reference table of audience profiles, you must:
1. Analyze the story content — who does it affect? what domain is it in?
2. Match it to the SINGLE best audience from the profiles table.
3. Output a writing brief (tone + focus + CTA) tailored to that audience.
4. Output a visual style brief: 2-3 color tones + lighting mood + overall feel. Keep it short (~20 words). Do NOT list specific scenes or objects — just the aesthetic direction.
5. Extract ONE single visual anchor from the story — the most striking, concrete detail (a place, an object, a moment). Not a list of scenes. One powerful image in one sentence.
6. ANONYMITY RULE: If describing people, use ONLY anonymous depictions — silhouettes, hands, backs of heads. NEVER name real individuals.

VISUAL PHILOSOPHY — Less Is More:
- The campaign images use a minimalist design language: one subject, expansive negative space, restrained palette.
- Your visual_style and visual_elements should support this — give the Image Generator a clear, focused direction, not a shopping list of elements.
- Do NOT suggest multiple metaphors, symbols, or scenes. One anchor is enough.

Rules:
- Choose the audience whose trigger keywords and focus area BEST match the story content.
- If no audience is a strong match, default to "general_public".
- The audience_brief must give the Writer enough direction to adapt tone and CTA.
- The visual_elements must be grounded in the story — never invent details not in the source material.
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
                "visual_elements": "",
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

        # User creative guidance from trend review HITL
        user_guidance = state.get("user_guidance")
        if user_guidance:
            messages.append(HumanMessage(content=(
                f"USER CREATIVE DIRECTION: The user has provided the following guidance "
                f"for this campaign. Factor this into your audience selection, visual style, "
                f"and visual elements decisions:\n{user_guidance}"
            )))

        # Refinement feedback from user (after final review)
        audience_feedback = state.get("audience_feedback")
        if audience_feedback:
            previous_audience = state.get("target_audience", "unknown")
            messages.append(HumanMessage(content=(
                f"REFINEMENT: The previous audience was '{previous_audience}'. "
                f"The user wants to change the targeting. Their feedback:\n{audience_feedback}\n\n"
                f"Choose a different or adjusted audience based on this feedback."
            )))

        decision: AudienceDecision = self.llm.invoke(messages)
        print(f"--- AUDIENCE ANALYZER: Selected '{decision.target_audience}' | Reason: {decision.reasoning} ---")

        return {
            "target_audience": decision.target_audience,
            "audience_brief": decision.audience_brief,
            "visual_style": decision.visual_style,
            "visual_elements": decision.visual_elements,
            "audience_feedback": None,   # Clear feedback after use
            "status": "audience_approved",
        }
