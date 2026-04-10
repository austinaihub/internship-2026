from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState

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
        retry_instruction = "The user rejected your previous draft. You MUST write a completely new and different post. Do not use the exact same phrasing as your first attempt." if is_retry else ""

        writer_prompt = state.get("writer_prompt")
        
        if not writer_prompt:
            return {"post_text": "Error: Missing writer prompt.", "status": "error"}

        is_retry = state.get("post_text") == "REJECTED"
        retry_instruction = "\n\nThe user rejected your previous draft. You MUST write a completely new and different post. Do not use the exact same phrasing as your first attempt." if is_retry else ""

        # Using direct ChatMessage invoking since the prompt is now pre-assembled
        from langchain_core.messages import SystemMessage, HumanMessage
        
        system_instruction = SystemMessage(content='''
You are an ethical and responsible creative writer for a Human Trafficking Awareness campaign.
Write a compelling, empowering social media post based ONLY on the provided topic and context instructions.

STRICT CRITERIA:
- Must feature data-driven facts and Verified Statistics from the context provided.
- Include 3 relevant hashtags.

You MUST adhere strictly to the "Language Matters" and Structural instructions below.

STRICT POST STRUCTURE (EVERY POST MUST FOLLOW THIS 4-PART FORMAT):
1. HOOK: A surprising fact or question.
2. EDUCATE: One verified fact or sign.
3. EMPOWER: One clear action to take.
4. SOURCE: Citation for the statistics.

LANGUAGE MATTERS (DO NOT USE THESE WORDS EVER):
- INSTEAD OF "Sex slave", USE "Survivor of sex trafficking"
- INSTEAD OF "Child prostitute", USE "Child victim of sex trafficking"
- INSTEAD OF "Rescued", USE "Identified" or "Supported"
- INSTEAD OF "Sold her body", USE "Was exploited" or "Was trafficked"
- INSTEAD OF "Illegal immigrant", USE "Undocumented individual"
- INSTEAD OF Always using "Victim", USE "Survivor" (when out of situation)
- INSTEAD OF "The trafficking problem", USE "Trafficking affects [center people]"
        ''')
        
        final_instructions = writer_prompt + retry_instruction
        
        response = self.llm.invoke([
            system_instruction,
            HumanMessage(content=final_instructions)
        ])
        
        return {
            "post_text": response.content,
            "status": "approving_text" # Interpretation: Next step is approval
        }
