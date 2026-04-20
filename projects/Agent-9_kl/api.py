"""
FastAPI backend for Campaign Agent React frontend.
Wraps the existing LangGraph workflow with REST endpoints.
"""

import os
import datetime
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.workflow.graph import create_graph

# ---------------------------------------------------------------------------
# App & CORS
# ---------------------------------------------------------------------------

app = FastAPI(title="Campaign Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory session store (single-user mode, same as Streamlit approach)
# ---------------------------------------------------------------------------

sessions: dict = {}  # {session_id: {"app": graph, "thread_id": str, "config": dict}}


def _get_session(session_id: str):
    """Retrieve a session or raise 404."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return sessions[session_id]


def _serialize_state(state: dict) -> dict:
    """
    Make the AgentState JSON-serializable.
    Strips non-serializable fields like LangChain messages.
    """
    safe = {}
    for key, value in state.items():
        if key == "messages":
            continue  # Skip BaseMessage objects
        safe[key] = value
    return safe


def _run_until_interrupt(session: dict, initial_state=None):
    """
    Stream the graph until it hits an interrupt or ends.
    Returns the current state snapshot.
    """
    graph = session["app"]
    config = session["config"]

    if initial_state is not None:
        for _ in graph.stream(initial_state, config, stream_mode="values"):
            pass
    else:
        for _ in graph.stream(None, config, stream_mode="values"):
            pass

    snapshot = graph.get_state(config)
    return snapshot


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class StartRequest(BaseModel):
    keywords: Optional[str] = None


class ApproveTrendRequest(BaseModel):
    action: str  # "approve" | "re-search"
    custom_topic: Optional[str] = None
    selected_article_title: Optional[str] = None
    guidance: Optional[str] = None  # Optional creative direction for downstream agents


class ApproveAudienceRequest(BaseModel):
    action: str  # "approve" | "edit"
    target_audience: Optional[str] = None
    audience_brief: Optional[str] = None
    visual_style_preset: Optional[str] = None  # rembrandt | editorial_flat | fog_silence | cinematic_depth
    visual_style: Optional[str] = None
    visual_elements: Optional[str] = None
    guidance: Optional[str] = None  # Updated creative direction


class ApproveImageRequest(BaseModel):
    action: str  # "approve" | "reject"
    feedback: Optional[str] = None


class RefineRequest(BaseModel):
    target: str  # "text_only" | "image_only" | "both" | "audience"
    feedback: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/campaign/start")
def start_campaign(req: StartRequest):
    """Start a new campaign. Optionally provide search keywords."""
    thread_id = datetime.datetime.now().strftime("ID-%m%d-%H%M%S")
    session_id = thread_id  # Use thread_id as session_id for simplicity

    graph = create_graph()
    config = {
        "configurable": {"thread_id": thread_id},
        "run_name": f"Campaign Agent Campaign {thread_id}"
    }

    session = {"app": graph, "thread_id": thread_id, "config": config}
    sessions[session_id] = session

    keywords = req.keywords.strip() if req.keywords and req.keywords.strip() else None
    initial_state = {
        "status": "starting",
        "user_search_keywords": keywords,
    }

    try:
        snapshot = _run_until_interrupt(session, initial_state)
        return {
            "session_id": session_id,
            "state": _serialize_state(snapshot.values),
            "has_next": bool(snapshot.next),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/campaign/{session_id}/state")
def get_campaign_state(session_id: str):
    """Get the current state of a campaign."""
    session = _get_session(session_id)
    snapshot = session["app"].get_state(session["config"])
    return {
        "state": _serialize_state(snapshot.values),
        "has_next": bool(snapshot.next),
    }


@app.post("/api/campaign/{session_id}/approve-trend")
def approve_trend(session_id: str, req: ApproveTrendRequest):
    """
    Handle trend review HITL checkpoint.
    Actions: 'approve' (with optional topic override) or 're-search'.
    """
    session = _get_session(session_id)
    graph = session["app"]
    config = session["config"]

    if req.action == "re-search":
        graph.update_state(config, {
            "trend_topic": None,
            "trend_context": None,
            "raw_news": None,
            "all_retrieved_news": None,
            "status": "starting",
        })
        snapshot = _run_until_interrupt(session)
        return {
            "state": _serialize_state(snapshot.values),
            "has_next": bool(snapshot.next),
        }

    # --- Approve ---
    update = {"status": "approved_trend"}
    current_state = graph.get_state(config).values
    all_news = current_state.get("all_retrieved_news", [])

    if req.custom_topic and req.custom_topic.strip():
        # User typed a custom topic — re-extract context via LLM
        update["trend_topic"] = req.custom_topic.strip()
        update["trend_context"] = _re_extract_context(
            topic=req.custom_topic.strip(),
            articles=all_news,
            system_instruction=(
                "Given the user's chosen topic and the available articles below, "
                "write a detailed 'who, what, when, where, why' context summary "
                "relevant to the topic. If no article matches well, summarize based "
                "on the topic alone."
            )
        )

    elif req.selected_article_title and req.selected_article_title.strip():
        # User picked a specific article — re-extract context
        chosen = next(
            (a for a in all_news if a.get("title") == req.selected_article_title),
            None
        )
        if chosen:
            update["trend_topic"] = chosen.get("title", req.selected_article_title)
            update["trend_context"] = _re_extract_context(
                topic=chosen.get("title", ""),
                articles=[chosen],
                system_instruction=(
                    "Write a detailed 'who, what, when, where, why' context summary "
                    "for the following human trafficking news article. Focus on why "
                    "it matters for public awareness."
                )
            )
        else:
            update["trend_topic"] = req.selected_article_title.strip()

    # else: keep AI recommendation as-is

    # Inject user guidance if provided
    if req.guidance and req.guidance.strip():
        update["user_guidance"] = req.guidance.strip()

    graph.update_state(config, update)
    snapshot = _run_until_interrupt(session)
    return {
        "state": _serialize_state(snapshot.values),
        "has_next": bool(snapshot.next),
    }


def _re_extract_context(topic: str, articles: list, system_instruction: str) -> str:
    """Use LLM to re-extract trend_context for a user-selected topic/article."""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage

    refiner = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    article_texts = "\n\n".join([
        f"Title: {a.get('title')}\nSource: {a.get('source')}\nURL: {a.get('url')}"
        for a in articles
    ])
    resp = refiner.invoke([
        SystemMessage(content=system_instruction),
        HumanMessage(content=f"User Topic: {topic}\n\nAvailable Articles:\n{article_texts}")
    ])
    return resp.content


@app.post("/api/campaign/{session_id}/approve-audience")
def approve_audience(session_id: str, req: ApproveAudienceRequest):
    """
    Handle audience review HITL checkpoint.
    Actions:
      'approve' — accept audience decision as-is
      'edit'    — override audience fields with user-provided values (hard override, no LLM)
    """
    session = _get_session(session_id)
    graph = session["app"]
    config = session["config"]

    update = {"status": "audience_approved"}

    if req.action == "edit":
        # Hard override — directly patch state fields, bypassing LLM
        if req.target_audience and req.target_audience.strip():
            update["target_audience"] = req.target_audience.strip()
        if req.audience_brief and req.audience_brief.strip():
            update["audience_brief"] = req.audience_brief.strip()
        if req.visual_style_preset and req.visual_style_preset.strip():
            update["visual_style_preset"] = req.visual_style_preset.strip()
        if req.visual_style and req.visual_style.strip():
            update["visual_style"] = req.visual_style.strip()
        if req.visual_elements and req.visual_elements.strip():
            update["visual_elements"] = req.visual_elements.strip()

    # Style preset can also be changed in approve mode (without editing other fields)
    if req.action == "approve" and req.visual_style_preset and req.visual_style_preset.strip():
        update["visual_style_preset"] = req.visual_style_preset.strip()

    # Update or add user guidance if provided
    if req.guidance and req.guidance.strip():
        update["user_guidance"] = req.guidance.strip()

    graph.update_state(config, update)
    snapshot = _run_until_interrupt(session)
    return {
        "state": _serialize_state(snapshot.values),
        "has_next": bool(snapshot.next),
    }


@app.post("/api/campaign/{session_id}/approve-image")
def approve_image(session_id: str, req: ApproveImageRequest):
    """
    Handle image review HITL checkpoint.
    Actions:
      'approve'              — publish the campaign
      'regen_image'          — regenerate image only (keep text)
      'regen_text_and_image'  — regenerate both text and image (re-run from writer)
    """
    session = _get_session(session_id)
    graph = session["app"]
    config = session["config"]

    if req.action == "approve":
        graph.update_state(config, {"status": "publisher"})

    elif req.action == "regen_image":
        # Only regenerate image — keep text, clear image
        graph.update_state(config, {
            "image_path": "REJECTED",
            "image_feedback": req.feedback or "",
        })

    elif req.action == "regen_text_and_image":
        # Regenerate text + image — clear both, re-run from writer
        graph.update_state(config, {
            "post_text": "REJECTED",
            "image_path": "REJECTED",
            "text_feedback": req.feedback or "",
            "image_feedback": "",
        })

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {req.action}")

    snapshot = _run_until_interrupt(session)
    return {
        "state": _serialize_state(snapshot.values),
        "has_next": bool(snapshot.next),
    }


@app.post("/api/campaign/{session_id}/refine")
def refine_campaign(session_id: str, req: RefineRequest):
    """
    Refinement loop: create a new session pre-filled with existing state,
    only clearing the fields that need regeneration.
    """
    session = _get_session(session_id)
    current_state = session["app"].get_state(session["config"]).values

    # Create new session
    new_thread_id = datetime.datetime.now().strftime("ID-%m%d-%H%M%S")
    new_session_id = new_thread_id
    new_graph = create_graph()
    new_config = {
        "configurable": {"thread_id": new_thread_id},
        "run_name": f"Campaign Agent Refine {new_thread_id}"
    }
    new_session = {"app": new_graph, "thread_id": new_thread_id, "config": new_config}
    sessions[new_session_id] = new_session

    # Build pre-filled state — always keep trend data
    prefilled = {
        "trend_topic": current_state.get("trend_topic"),
        "trend_context": current_state.get("trend_context"),
        "raw_news": current_state.get("raw_news"),
        "all_retrieved_news": current_state.get("all_retrieved_news"),
    }

    if req.target == "text_only":
        # Audience already set → skip audience_analyzer, go directly to writer
        prefilled.update({
            "target_audience": current_state.get("target_audience"),
            "audience_brief": current_state.get("audience_brief"),
            "visual_style": current_state.get("visual_style"),
            "visual_elements": current_state.get("visual_elements"),
            "post_text": None,
            "image_path": current_state.get("image_path"),
            "overlay_text": current_state.get("overlay_text"),
            "text_feedback": req.feedback,
            "status": "audience_approved",
        })
    elif req.target == "image_only":
        # Audience already set → skip audience_analyzer, go directly to writer→image
        prefilled.update({
            "target_audience": current_state.get("target_audience"),
            "audience_brief": current_state.get("audience_brief"),
            "visual_style": current_state.get("visual_style"),
            "visual_elements": current_state.get("visual_elements"),
            "post_text": current_state.get("post_text"),
            "image_path": None,
            "image_feedback": req.feedback,
            "status": "audience_approved",
        })
    elif req.target == "both":
        # Audience already set → skip audience_analyzer, go directly to writer
        prefilled.update({
            "target_audience": current_state.get("target_audience"),
            "audience_brief": current_state.get("audience_brief"),
            "visual_style": current_state.get("visual_style"),
            "visual_elements": current_state.get("visual_elements"),
            "post_text": None,
            "image_path": None,
            "text_feedback": req.feedback,
            "status": "audience_approved",
        })
    elif req.target == "audience":
        # Audience needs re-analysis → go through audience_analyzer (will interrupt for review)
        prefilled.update({
            "target_audience": None,
            "audience_brief": None,
            "visual_style": None,
            "visual_elements": None,
            "post_text": None,
            "image_path": None,
            "audience_feedback": req.feedback,
            "status": "approved_trend",
        })
    else:
        raise HTTPException(status_code=400, detail=f"Unknown refine target: {req.target}")

    try:
        snapshot = _run_until_interrupt(new_session, prefilled)
        return {
            "session_id": new_session_id,
            "state": _serialize_state(snapshot.values),
            "has_next": bool(snapshot.next),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/campaign/image/{filename}")
def get_image(filename: str):
    """Serve generated images from the outputs directory."""
    output_dir = os.getenv("OUTPUT_DIR", "outputs")
    filepath = os.path.normpath(os.path.join(output_dir, filename))

    # Security: ensure the path stays within outputs/
    if not filepath.startswith(os.path.normpath(output_dir)):
        raise HTTPException(status_code=403, detail="Access denied.")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found.")

    return FileResponse(filepath, media_type="image/png")
