import os
import json
from pathlib import Path
from dotenv import load_dotenv

# 1. Setup Environment
# Load .env from the same directory as this script
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

from src.state import AgentState
from src.agents.trend_analyzer import TrendAnalyzer
from src.agents.planner import PlannerAgent
from src.agents.writer import WriterAgent
from src.agents.image_generator import ImageGeneratorAgent
from src.agents.publisher import PublisherAgent

def print_header(title):
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80)

def print_json(label, data):
    print(f"\n>>> {label}:")
    # Clean up large news content for readability in terminal
    display_data = {}
    if isinstance(data, dict):
        for k, v in data.items():
            if k in ["all_retrieved_news", "raw_news"] and isinstance(v, list):
                display_data[k] = f"[{len(v)} articles retrieved]"
            elif k == "trend_context" and v and len(v) > 500:
                display_data[k] = v[:500] + "... [TRUNCATED]"
            else:
                display_data[k] = v
    else:
        display_data = data
        
    print(json.dumps(display_data, indent=2))

def run_debug():
    print_header("AGENT-8 DEBUGGING SESSION")
    
    # Initialize all agents
    try:
        trend_analyzer = TrendAnalyzer()
        planner = PlannerAgent()
        writer = WriterAgent()
        image_gen = ImageGeneratorAgent()
        publisher = PublisherAgent()
        print("Successfully initialized all agents.")
    except Exception as e:
        print(f"Initialization Error: {e}")
        return

    # Initial State
    state: AgentState = {
        "status": "starting",
        "trend_topic": None,
        "trend_context": None,
        "raw_news": None,
        "all_retrieved_news": None,
        "writer_prompt": None,
        "post_text": None,
        "image_prompt": None,
        "image_path": None,
        "image_feedback": None,
        "feedback": None
    }

    # --- STEP 1: TREND ANALYZER ---
    print_header("STEP 1: Trend Analyzer")
    print_json("INPUT TO TREND ANALYZER", state)
    try:
        trend_updates = trend_analyzer.analyze_trends(state)
        state.update(trend_updates)
        print_json("OUTPUT FROM TREND ANALYZER", trend_updates)
    except Exception as e:
        print(f"FAILED at Trend Analyzer: {e}")
        return

    # --- STEP 2: PLANNER (Pre-Writer) ---
    print_header("STEP 2: Planner (Decision 1)")
    print_json("INPUT TO PLANNER", state)
    plan_updates = planner.plan_next_step(state)
    state.update(plan_updates)
    print_json("OUTPUT FROM PLANNER", plan_updates)

    # --- STEP 3: WRITER ---
    if state.get("writer_prompt") and "writing" in state.get("status", "") or "approving" in state.get("status", ""):
        print_header("STEP 3: Writer")
        # In a real run, status might be 'approving_prompt'. 
        # We manually force it to 'writing' for this debug script to ensure the agent runs.
        print_json("INPUT TO WRITER", state)
        try:
            writer_updates = writer.write_post(state)
            state.update(writer_updates)
            print_json("OUTPUT FROM WRITER", writer_updates)
        except Exception as e:
            print(f"FAILED at Writer: {e}")
            return

    # --- STEP 4: PLANNER (Post-Writer) ---
    print_header("STEP 4: Planner (Decision 2)")
    plan_updates = planner.plan_next_step(state)
    state.update(plan_updates)
    print_json("OUTPUT FROM PLANNER", plan_updates)

    # --- STEP 5: IMAGE GENERATOR ---
    if state.get("post_text") and state.get("status") == "generating_image":
        print_header("STEP 5: Image Generator")
        print_json("INPUT TO IMAGE GENERATOR", state)
        try:
            image_updates = image_gen.generate_image(state)
            state.update(image_updates)
            print_json("OUTPUT FROM IMAGE GENERATOR", image_updates)
        except Exception as e:
            print(f"FAILED at Image Generator: {e}")
            # We don't return here so we can see the full state
            state["status"] = "error"
            state["feedback"] = str(e)

    # --- STEP 6: PUBLISHER ---
    if state.get("status") == "publisher" or (state.get("post_text") and state.get("image_path")):
        print_header("STEP 6: Publisher")
        print_json("INPUT TO PUBLISHER", state)
        try:
            pub_updates = publisher.publish_post(state)
            state.update(pub_updates)
            print_json("OUTPUT FROM PUBLISHER", pub_updates)
        except Exception as e:
            print(f"FAILED at Publisher: {e}")

    print_header("DEBUG SESSION COMPLETE")
    print_json("FINAL AGENT STATE", state)

if __name__ == "__main__":
    run_debug()
