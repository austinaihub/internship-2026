from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState

WRITER_SYSTEM_PROMPT = """
You write social media posts for a Human Trafficking Awareness campaign.

POST STRUCTURE (mandatory 4-part format):
1. HOOK — A surprising statistic or provocative question.
2. EDUCATE — One verified fact or warning sign from the source material.
3. EMPOWER — One concrete action the reader can take.
4. SOURCE — Cite the original article/statistic.

End with 3 relevant hashtags.

LANGUAGE RULES (never violate):
- "survivor of sex trafficking" not "sex slave"
- "child victim of sex trafficking" not "child prostitute"
- "identified" / "supported" not "rescued"
- "was exploited" / "was trafficked" not "sold her body"
- "undocumented individual" not "illegal immigrant"
- "survivor" (when out of situation) not always "victim"
- "trafficking affects [people]" not "the trafficking problem"
"""


class WriterAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    def write_post(self, state: AgentState):
        """
        Generates a social media post based on the trend.
        """
        print("--- WRITER: Generating post draft ---")
        
        topic = state.get("trend_topic")
        context = state.get("trend_context")
        
        if not topic or not context:
            return {"post_text": "Error: Missing topic or context.", "status": "error"}

        is_retry = state.get("post_text") == "REJECTED"
        retry_instruction = "\n\nThe previous draft was rejected. Write a COMPLETELY DIFFERENT post — new angle, new phrasing." if is_retry else ""

        # Refinement feedback from user (after final review)
        text_feedback = state.get("text_feedback")
        refinement_instruction = ""
        if text_feedback:
            previous_text = state.get("post_text", "")
            refinement_instruction = (
                f"\n\nREFINEMENT MODE — The user reviewed the previous post and wants changes."
                f"\n\nPREVIOUS POST:\n{previous_text}"
                f"\n\nUSER FEEDBACK: {text_feedback}"
                f"\n\nRevise the post based on this feedback. Keep what works, fix what the user pointed out."
            )

        from langchain_core.messages import SystemMessage, HumanMessage
        
        system_msg = SystemMessage(content=WRITER_SYSTEM_PROMPT)
        
        human_content = f"Topic: {topic}\nContext: {context}"
        
        # Inject audience targeting if available
        audience_brief = state.get("audience_brief")
        if audience_brief:
            human_content += f"\nTarget Audience: {state.get('target_audience')}\nAudience Brief: {audience_brief}"
        
        # User creative guidance from trend review HITL
        user_guidance = state.get("user_guidance")
        if user_guidance:
            human_content += f"\n\nUSER CREATIVE DIRECTION: {user_guidance}"

        human_content += retry_instruction
        human_content += refinement_instruction
        
        # If user provided a custom writer_prompt via HITL, use it as the human message instead
        writer_prompt = state.get("writer_prompt")
        if writer_prompt:
            human_content = writer_prompt + retry_instruction + refinement_instruction
        
        response = self.llm.invoke([
            system_msg,
            HumanMessage(content=human_content)
        ])
        
        return {
            "post_text": response.content,
            "text_feedback": None,       # Clear feedback after use
            "status": "approved_text"
        }
