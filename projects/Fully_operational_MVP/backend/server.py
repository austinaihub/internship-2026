from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import datetime
import uuid
import asyncio

# Set up LangSmith / Env
from dotenv import load_dotenv
load_dotenv()

from src.workflow.graph import create_graph

app = FastAPI(title="Agent-8 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

# Global graph instance
agent_app = create_graph()

# Serve static output files
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

class StartRequest(BaseModel):
    manual_url: Optional[str] = None

class FeedbackRequest(BaseModel):
    state_updates: Dict[str, Any]

def run_until_human(config: dict):
    # LangGraph stops at all defined interrupts. We must continuously stream 
    # until we hit a state that actually asks for human approval to avoid hanging.
    while True:
        events = list(agent_app.stream(None, config, stream_mode="values"))
        
        # Determine if there are more steps
        state_snap = agent_app.get_state(config)
        if not state_snap.next:
            break # Graph finished
            
        current_status = state_snap.values.get("status", "")
        if current_status in ["approving_prompt", "approving_text", "approving_image", "done", "error"]:
            break # Waiting for human
            

@app.post("/api/workflow/start")
async def start_workflow(req: StartRequest):
    thread_id = f"ID-{datetime.datetime.now().strftime('%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}, "run_name": f"Agent-8 Campaign {thread_id}"}
    
    initial_state = {"status": "starting"}
    if req.manual_url and req.manual_url.strip():
        initial_state["manual_url"] = req.manual_url.strip()
        
    try:
        agent_app.update_state(config, initial_state)
        # Background the execution into a dedicated OS thread so it does not block FastAPI routing capabilities
        asyncio.create_task(asyncio.to_thread(run_until_human, config))
        return {"thread_id": thread_id, "message": "Workflow started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workflow/{thread_id}/state")
async def get_state(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = agent_app.get_state(config).values
        return {"state": state}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Thread not found or error retrieving state")

@app.post("/api/workflow/{thread_id}/feedback")
async def submit_feedback(thread_id: str, req: FeedbackRequest):
    config = {"configurable": {"thread_id": thread_id}, "run_name": f"Agent-8 Campaign {thread_id}"}
    try:
        agent_app.update_state(config, req.state_updates)
        # Background the execution into a dedicated OS thread so the API responds instantly and doesn't exhaust ThreadPool!
        asyncio.create_task(asyncio.to_thread(run_until_human, config))
        return {"message": "Feedback applied and workflow resumed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
