import os
import base64
import google.generativeai as genai
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from src.state import AgentState

class ImageGeneratorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        # Initialize Google GenAI client (requires GEMINI_API_KEY environment variable)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY is not set. Nano Banana generation will fail.")
        genai.configure(api_key=api_key)

    @traceable(name="Nano Banana (Gemini) Image Generation")
    def generate_image(self, state: AgentState):
        """
        Generates an image based on the post text using Gemini (Nano Banana).
        """
        print("--- IMAGE GENERATOR: Creating visual prompt for Nano Banana ---")
        
        post_text = state.get("post_text")
        if not post_text:
            return {"status": "error", "feedback": "No post text available."}

        # 1. Generate Image Prompt
        prompt_maker = ChatPromptTemplate.from_template(
            """
            You are an expert AI Design Director specializing in ethical, Safety-by-Design visuals for human trafficking awareness.
            Create a highly specific image generation prompt to accompany the following social media post text.
            The generation model is literal (Google's Gemini Image model).
            
            Post Text:
            {text}
            
            STRICT VISUAL POLICIES (NEVER VIOLATE THESE):
            - NEVER include AI-generated faces, bodies, or people.
            - NEVER include children in any context.
            - NEVER include physical restraints (chains, ropes, handcuffs, bars, cages).
            - NEVER use dark alleys, rain, or cinematic despair aesthetics.
            - NEVER include cowering, crying, distressed figures, or depictions of physical abuse/bruises.
            
            APPROVED IMAGERY CATEGORIES (USE THESE INSTEAD):
            - Clean, bold Typography-driven designs (e.g. bold numbers/quotes filling the space).
            - Data visualization, infographics, maps, or charts.
            - Abstract/Symbolic imagery (light breaking through, open doors, community silhouettes).
            - Empty, everyday locations (airports, nail salons, construction sites - no people).
            - Flat-design icons or simple illustrations.
            
            Write a detailed prompt string relying ONLY on the Approved Imagery Categories. 
            Prioritize clean, empowering, data-driven or abstract symbolic visuals.
            
            Return ONLY the prompt string.
            """
        )
        
        chain = prompt_maker | self.llm
        image_prompt = chain.invoke({"text": post_text}).content
        
        feedback = state.get("image_feedback")
        if feedback:
            image_prompt += f"\nCRITICAL INSTRUCTION FROM USER FOR REGENERATION: {feedback}"
            
        print(f"Generated Image Prompt: {image_prompt}")

        # 2. Generate Image via Subprocess
        print("--- IMAGE GENERATOR: Calling Nano Banana (Gemini) API via Isolated Subprocess ---")
        
        try:
            # Save locally for reference
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_image_{timestamp}.png"
            output_dir = os.getenv("OUTPUT_DIR", "outputs")
            filepath = os.path.join(output_dir, filename)
            os.makedirs(output_dir, exist_ok=True)
            
            import subprocess
            import sys
            
            isolated_script = os.path.join(os.path.dirname(__file__), "isolated_gemini.py")
            env = os.environ.copy()
            
            # Subprocess isolation completely bypasses FastAPI's Uvicorn threading pool, preventing the 
            # critical GRPC infinite freeze that occurs with Google's deprecated model inside async servers
            proc = subprocess.run(
                [sys.executable, isolated_script, image_prompt, filepath],
                capture_output=True, text=True, env=env, timeout=60
            )
            
            if proc.returncode != 0 or "SUCCESS" not in proc.stdout:
                print(f"Isolated Script Output: {proc.stdout}\nErrors: {proc.stderr}")
                raise Exception("Nano Banana subprocess crashed or returned non-zero.")
                
            print(f"Successfully generated offline image directly identical to Agent-8 prototype: {filepath}")
                    
            # Map the local file path dynamically to the new unified API port so Next.js seamlessly reads the old protocol logic
            network_path = f"http://127.0.0.1:8002/{filepath.replace(os.sep, '/')}"
            return {
                "image_prompt": image_prompt,
                "image_path": network_path, 
                "status": "approving_image"
            }
        except Exception as e:
            print(f"ERROR: Image Generation Failed using Nano Banana: {e}")
            
            # Secure Fallback to prevent UI freeze if Google's beta endpoint rejects/fails the prompt
            dummy_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
            dummy_uri = f"data:image/png;base64,{dummy_b64}"
            
            return {
                "image_prompt": image_prompt,
                "image_path": dummy_uri,
                "image_feedback": f"API FAILURE: {str(e)}",
                "status": "approving_image"
            }
