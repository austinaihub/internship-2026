import os
from datetime import datetime
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
            print("WARNING: GEMINI_API_KEY is not set.")
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

        # 2. Generate Image
        print("--- IMAGE GENERATOR: Calling Nano Banana (Gemini) API ---")
        # Initialize the GenerativeModel per the user's provided SDK instructions
        model = genai.GenerativeModel('gemini-3.1-flash-image-preview')
        
        try:
            result = model.generate_content(
                image_prompt,
                # Force the model to output an image instead of text
                generation_config={"response_modalities": ["IMAGE"]}
            )
            
            # The result contains the parts with an image (using save as shown in docs, or raw bytes)
            generated_image_part = result.parts[0]
            
            # Save locally for reference
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_image_{timestamp}.png"
            output_dir = os.getenv("OUTPUT_DIR", "outputs")
            filepath = os.path.join(output_dir, filename)
            os.makedirs(output_dir, exist_ok=True)
            
            # Depending on the SDK returned object, image data is usually in inline_data
            if hasattr(generated_image_part, 'inline_data') and generated_image_part.inline_data:
                with open(filepath, 'wb') as f:
                    f.write(generated_image_part.inline_data.data)
            else:
                print(f"ERROR: Unrecognized format for image part: {generated_image_part}")
                    
            print(f"Image saved to {filepath}")
            
            return {
                "image_prompt": image_prompt,
                "image_path": filepath, # Storing local path for Publisher
                "status": "approving_image"
            }
        except Exception as e:
            print(f"ERROR: Image Generation Failed: {e}")
            return {
                "image_prompt": image_prompt,
                "image_path": None,
                "status": "error"
            }
