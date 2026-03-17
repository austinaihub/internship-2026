from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.agents.supervisor import SupervisorAgent
from src.agents.trend_analyzer import TrendAnalyzer
from src.agents.audience_analyzer import AudienceAnalyzer
from src.agents.writer import WriterAgent
from src.agents.image_generator import ImageGeneratorAgent
from src.agents.publisher import PublisherAgent

def create_graph():
    # Initialize agents
    supervisor_agent = SupervisorAgent()
    trend_analyzer   = TrendAnalyzer()
    audience_agent   = AudienceAnalyzer()
    writer_agent     = WriterAgent()
    image_gen_agent  = ImageGeneratorAgent()
    publisher_agent  = PublisherAgent()

    workflow = StateGraph(AgentState)

    # ── Nodes ──────────────────────────────────────────────────────────────────
    workflow.add_node("supervisor",        supervisor_agent.route)
    workflow.add_node("trend_analyzer",    trend_analyzer.analyze_trends)
    workflow.add_node("audience_analyzer", audience_agent.analyze_audience)
    workflow.add_node("writer",            writer_agent.write_post)
    workflow.add_node("image_generator",   image_gen_agent.generate_image)
    workflow.add_node("publisher",         publisher_agent.publish_post)

    # ── Entry: START → Supervisor ──────────────────────────────────────────────
    workflow.add_edge(START, "supervisor")

    # ── Supervisor conditional routing ─────────────────────────────────────────
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state["next"],
        {
            "trend_analyzer":    "trend_analyzer",
            "audience_analyzer": "audience_analyzer",
            "writer":            "writer",
            "image_generator":   "image_generator",
            "publisher":         "publisher",
            "FINISH":            END,
        }
    )

    # ── All workers report back to Supervisor ──────────────────────────────────
    workflow.add_edge("trend_analyzer",    "supervisor")
    workflow.add_edge("audience_analyzer", "supervisor")
    workflow.add_edge("writer",            "supervisor")
    workflow.add_edge("image_generator",   "supervisor")
    workflow.add_edge("publisher",         END)   # publisher always finishes

    # ── Compile with HITL interrupts ───────────────────────────────────────────
    from langgraph.checkpoint.memory import MemorySaver
    memory = MemorySaver()

    app = workflow.compile(
        checkpointer=memory,
        interrupt_after=["audience_analyzer", "writer", "image_generator"]
    )

    return app
