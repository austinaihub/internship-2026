from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.agents.trend_analyzer import TrendAnalyzer
from src.agents.planner import PlannerAgent
from src.agents.writer import WriterAgent
from src.agents.image_generator import ImageGeneratorAgent
from src.agents.publisher import PublisherAgent

def create_graph():
    # Initialize implementation instances
    trend_analyzer = TrendAnalyzer()
    planner_agent = PlannerAgent()
    writer_agent = WriterAgent()
    image_gen_agent = ImageGeneratorAgent()
    publisher_agent = PublisherAgent()

    # Define the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("trend_analyzer", trend_analyzer.analyze_trends)
    workflow.add_node("planner", planner_agent.plan_next_step)
    workflow.add_node("writer", writer_agent.write_post)
    workflow.add_node("image_generator", image_gen_agent.generate_image)
    workflow.add_node("publisher", publisher_agent.publish_post)

    # Define edges
    # Start -> Trend Analyzer -> Planner
    workflow.set_entry_point("trend_analyzer")
    workflow.add_edge("trend_analyzer", "planner")

    # Functions to determine where to go next
    def route_step(state):
        trend = state.get("trend_topic")
        prompt = state.get("writer_prompt")
        text = state.get("post_text")
        image = state.get("image_path")
        status = state.get("status")
        
        if not trend:
            return "trend_analyzer"
        elif status in ["approving_prompt", "writing"] or not prompt or prompt == "REJECTED":
            return "writer"
        elif status == "generating_image" or not image or image == "REJECTED":
            return "image_generator"
        else:
            return "publisher"

    workflow.add_conditional_edges(
        "planner",
        route_step,
        {
            "trend_analyzer": "trend_analyzer",
            "writer": "writer",
            "image_generator": "image_generator",
            "publisher": "publisher"
        }
    )

    # Return to planner after each step to re-evaluate
    workflow.add_edge("writer", "planner")
    workflow.add_edge("image_generator", "planner")
    workflow.add_edge("publisher", END)

    # Compile with persistence (checkpointer) likely needed for interrupts, 
    # but for simple local script run, we can maybe just run it or use MemorySaver.
    from langgraph.checkpoint.memory import MemorySaver
    memory = MemorySaver()
    
    app = workflow.compile(
        checkpointer=memory,
        interrupt_after=["planner", "writer", "image_generator"]
    )
    
    return app
