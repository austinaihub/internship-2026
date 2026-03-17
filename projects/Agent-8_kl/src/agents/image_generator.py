import os
from datetime import datetime
from google import genai
from google.genai import types
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
        self.genai_client = genai.Client(api_key=api_key)

    @traceable(name="Nano Banana (Gemini) Image Generation")
    def generate_image(self, state: AgentState):
        """
        Generates an image based on the post text using Gemini (Nano Banana).
        """
        print("--- IMAGE GENERATOR: Creating visual prompt for Nano Banana ---")
        
        post_text = state.get("post_text")
        if not post_text:
            return {"status": "error", "feedback": "No post text available."}

        # 1. Get visual style and story context
        visual_style = state.get("visual_style") or "Cinematic teal-and-orange grade, dramatic chiaroscuro lighting, high-contrast bold typography, gritty urban texture."
        trend_topic = state.get("trend_topic") or ""
        trend_context = state.get("trend_context") or ""

        # 2. Generate Image Prompt — combines event information with visual style
        prompt_maker = ChatPromptTemplate.from_template(
            """
            You are a photography director creating an awareness poster that TELLS THE STORY of a real event.

            EVENT INFORMATION:
            Headline: {topic}
            Context: {context}
            Post Text: {text}

            VISUAL STYLE BRIEF (follow this art direction):
            {visual_style}

            STEP 1 — EXTRACT FROM THE EVENT (mandatory, these MUST appear as text on the final image):
            - HEADLINE: The event headline or a shortened version (max 8 words), rendered as large bold title text at the top or center.
            - KEY FACT: One specific statistic, date, or factual detail from the story (e.g. "3 convicted", "March 2026", "$2.4M seized"). Render as a prominent number or callout.
            - SOURCE LINE: A short attribution at the bottom (e.g. "Source: Reuters" or "via AP News"). Small, subtle text.

            STEP 2 — VISUAL DESIGN:

            SCENE: Build an environment that represents WHERE this specific event happened — a courtroom, a government building, a warehouse, a particular city's skyline, etc. The setting must be recognizable as connected to the story.

            FOCAL OBJECT: ONE hero object tied to THIS event — a gavel for a conviction, a legislative document for a new law, a factory machine for labor trafficking, a computer screen for online exploitation. It must feel specific, not generic.

            CAMERA: Real photography — focal length, aperture, angle, distance. Photojournalism meets poster.

            ATMOSPHERE: One environmental effect (dust, fog, light rays, condensation) that adds cinematic drama.

            SAFETY RULES (absolute):
            - ZERO people, faces, bodies, hands, or silhouettes
            - ZERO children in any form
            - ZERO worn restraints (handcuffs on wrists, cages with occupants)
            - ZERO violence, injury, abuse, or distress

            OUTPUT: Return ONLY the final image prompt as one dense paragraph. It MUST describe: (1) the text overlays with exact wording from the event, (2) the scene/environment, (3) the focal object, (4) camera and lighting, (5) atmosphere. The image should look like a news-documentary poster — informative AND cinematic.
            """
        )
        
        chain = prompt_maker | self.llm
        image_prompt = chain.invoke({
            "text": post_text,
            "topic": trend_topic,
            "context": trend_context,
            "visual_style": visual_style
        }).content
        
        feedback = state.get("image_feedback")
        if feedback:
            image_prompt += f"\nCRITICAL INSTRUCTION FROM USER FOR REGENERATION: {feedback}"
            
        print(f"Generated Image Prompt: {image_prompt}")

        # 2. Generate Image
        print("--- IMAGE GENERATOR: Calling Nano Banana (Gemini) API ---")

        try:
            result = self.genai_client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=[image_prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio="4:5", # Instagram portrait format
                        image_size="1K",# 1024px on the long edge
                    )
                )
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
