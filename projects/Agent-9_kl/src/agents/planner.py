from langchain_openai import ChatOpenAI
from src.state import AgentState

class PlannerAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)

    def plan_next_step(self, state: AgentState):
        """
        The Planner decides the next step based on the state.
        This function essentially acts as the router logic or a checkpoint logger.
        """
        print(f"--- PLANNER: Reviewing State ---")
        trend = state.get("trend_topic")
        text = state.get("post_text")
        image = state.get("image_path")
        prompt = state.get("writer_prompt")
        
        step = "unknown"
        update_dict = {}
        
        if not trend:
            step = "trend_analyzer"
        elif not prompt or prompt == "REJECTED":
            # Auto-generate the default prompt here and route to approving_prompt
            context = state.get("trend_context")
            default_prompt = (
                "You are an ethical and responsible creative writer for a Human Trafficking Awareness campaign.\n"
                "Write a compelling, empowering social media post based ONLY on the following trend.\n\n"
                f"Topic: {trend}\n"
                f"Context: {context}\n\n"
                "STRICT CRITERIA:\n"
                "- Must feature data-driven facts and Verified Statistics from the context provided.\n"
                "- Include 3 relevant hashtags."
            )
            update_dict["writer_prompt"] = default_prompt
            update_dict["status"] = "approving_prompt"
            step = "writer"
        elif not text or text == "REJECTED":
            update_dict["status"] = "writing"
            step = "writer"  # Route back to writer if missing or rejected
        elif not image or image == "REJECTED":
            update_dict["status"] = "generating_image"
            step = "image_generator"
        else:
            update_dict["status"] = "publisher"
            step = "publisher"
            
        print(f"Planner Decision: Proceed to {step}")
        if "status" not in update_dict:
            update_dict["status"] = step
        return update_dict
