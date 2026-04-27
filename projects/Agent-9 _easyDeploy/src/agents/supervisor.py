from typing import Literal, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from src.state import AgentState

# ---------------------------------------------------------------------------
# Routing Schema
# ---------------------------------------------------------------------------

WORKERS = Literal["trend_analyzer", "audience_analyzer", "writer", "image_generator", "publisher", "FINISH"]

class RouteDecision(BaseModel):
    next: WORKERS = Field(description="The next worker agent to invoke, or FINISH to end.")
    reasoning: str = Field(description="Brief explanation of why this worker was chosen.")


# ---------------------------------------------------------------------------
# Supervisor Agent
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
Route tasks in a Human Trafficking Awareness content pipeline.

Workers & preconditions:
- trend_analyzer → no trend_topic yet
- audience_analyzer → trend_topic exists AND status is NOT "approving_trend", target_audience missing
- writer → target_audience exists, post_text missing or REJECTED
- image_generator → post_text approved, image_path missing or REJECTED
- publisher → both post_text and image_path approved
- FINISH → status is "done" OR unrecoverable error (retry_count >= 2)

On error with retry_count < 2, retry the same worker.
Human-in-the-Loop steps are handled externally — never skip them.
"""


class SupervisorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(RouteDecision)

    @traceable(name="Supervisor Routing Decision")
    def route(self, state: AgentState) -> dict:
        """
        Reads the full pipeline state and decides which worker agent to call next.
        Returns {"next": "<agent>"} to drive LangGraph conditional routing.
        """
        trend = state.get("trend_topic")
        text = state.get("post_text")
        image = state.get("image_path")
        status = state.get("status", "starting")
        retry_counts = state.get("retry_counts") or {}

        # ── Deterministic fast-paths (avoid LLM hallucination) ─────────
        if status == "approving_trend":
            return {"next": "audience_analyzer"}
        if status == "approved_trend":
            return {"next": "audience_analyzer"}
        if status == "approving_audience":
            return {"next": "writer"}
        if status == "audience_approved":
            return {"next": "writer"}
        if status == "publisher":
            return {"next": "publisher"}
        if status == "approving_image":
            # Resumed from image review — check what needs regeneration
            if text == "REJECTED":
                return {"next": "writer"}
            if image == "REJECTED":
                return {"next": "image_generator"}

        # Build a plain-English state summary for the LLM
        audience = state.get("target_audience")

        state_summary = (
            f"status: {status}\n"
            f"trend_topic: {trend or 'None'}\n"
            f"target_audience: {audience or 'None'}\n"
            f"post_text: {'REJECTED' if text == 'REJECTED' else ('present' if text else 'None')}\n"
            f"image_path: {'REJECTED' if image == 'REJECTED' else ('present' if image else 'None')}\n"
            f"retry_counts: {retry_counts}"
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Current pipeline state:\n{state_summary}\n\nWhich worker should run next?")
        ]

        decision: RouteDecision = self.llm.invoke(messages)
        print(f"--- SUPERVISOR: Routing to '{decision.next}' | Reason: {decision.reasoning} ---")

        # Track retry counts per agent
        updated_retries = dict(retry_counts)
        if status == "error" and decision.next != "FINISH":
            updated_retries[decision.next] = updated_retries.get(decision.next, 0) + 1

        return {
            "next": decision.next,
            "retry_counts": updated_retries,
        }
