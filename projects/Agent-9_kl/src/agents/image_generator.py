import os
import textwrap
from datetime import datetime
from google import genai
from google.genai import types
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw, ImageFont
from src.state import AgentState

# ---------------------------------------------------------------------------
# Structured output for text extraction
# ---------------------------------------------------------------------------

class OverlayText(BaseModel):
    headline: str = Field(description="Event headline, max 8 words, punchy and informative.")
    key_fact: str = Field(description="One specific statistic, date, or factual detail, e.g. '3 convicted', 'March 2026', '$2.4M seized'.")
    source_line: str = Field(description="Short attribution, e.g. 'Source: Reuters' or 'via AP News'.")


# ---------------------------------------------------------------------------
# Font paths — shipped with the project
# ---------------------------------------------------------------------------

_FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "config", "fonts")

def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a project-bundled font with graceful fallback."""
    path = os.path.normpath(os.path.join(_FONT_DIR, name))
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        # Fallback: try system Arial, then default bitmap font
        for fallback in ["arial.ttf", "arialbd.ttf", "Arial.ttf"]:
            try:
                return ImageFont.truetype(fallback, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()


class ImageGeneratorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        self.text_extractor = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(OverlayText)
        # Initialize Google GenAI client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY is not set.")
        self.genai_client = genai.Client(api_key=api_key)

    # ------------------------------------------------------------------
    # Phase 1: Generate pure photography background (no text)
    # ------------------------------------------------------------------
    @traceable(name="Nano Banana (Gemini) Image Generation")
    def generate_image(self, state: AgentState):
        """
        Two-phase image generation:
        Phase 1 — Gemini generates a text-free cinematic photograph.
        Phase 2 — Pillow composites headline/facts/source onto the image.
        """
        print("--- IMAGE GENERATOR: Phase 1 — Creating visual prompt ---")

        post_text = state.get("post_text")
        if not post_text:
            return {"status": "error", "feedback": "No post text available."}

        visual_style = state.get("visual_style") or "Cinematic teal-and-orange grade, dramatic chiaroscuro lighting, gritty urban texture."
        visual_elements = state.get("visual_elements") or ""
        trend_topic = state.get("trend_topic") or ""
        trend_context = state.get("trend_context") or ""
        user_guidance = state.get("user_guidance") or ""

        # ── 1a. Generate image prompt (photography only, NO text) ──────────
        prompt_maker = ChatPromptTemplate.from_template(
            """
            You are a photography director for a Human Trafficking Awareness campaign.
            Your goal is to create powerful, emotionally resonant images that immediately
            evoke the reality of human trafficking — control, exploitation, lost freedom,
            and the fight for justice.

            ABSOLUTE RULE: All human figures must remain ANONYMOUS and unidentifiable.
            Preferred techniques: backs of heads, silhouettes against light,
            extreme close-ups on hands/feet, faces in deep shadow, bokeh-blurred
            figures, reflections in glass. No real person's likeness may ever appear.

            Minimal incidental text on objects (e.g. text on a passport, a sign) is acceptable, but do NOT render large headlines, captions, or decorative text in the scene.

            EVENT INFORMATION:
            Headline: {topic}
            Context: {context}
            Post Text: {text}

            VISUAL STYLE BRIEF (follow this art direction):
            {visual_style}

            VISUAL ANCHORS (mandatory — extracted from the real event):
            {visual_elements}
            You MUST incorporate the above visual anchors into your scene.
            These are the concrete, event-specific details that make this image unique.

            {user_guidance_block}

            DESIGN RULES:

            CRITICAL — DEPICT THE EVENT, NOT THE AUDIENCE: The image must show
            the SCENE WHERE THE TRAFFICKING EVENT HAPPENED — not the target audience's
            work environment. If the news is about migrants smuggled in lorries, show
            the lorries and the migrants, NOT lawmakers in a meeting room discussing it.
            Always ask: "What did this crime scene look like?" and depict THAT.

            SCENE: Build the environment using the VISUAL ANCHORS above. Use the exact
            location and setting details provided — do NOT substitute generic alternatives.
            Go BEYOND courtrooms and legal settings. Show WHERE trafficking actually
            happens: factories, motel rooms, cargo containers, construction sites,
            massage parlors, cramped apartments, city streets at night, small boats, lorries.

            EMOTIONAL CORE: The image must tell a HUMAN STORY about trafficking.
            Go beyond courtroom evidence and legal proceedings. Show the HUMAN IMPACT:
            - A person in a situation of control, confinement, or exploitation
            - The tension between captivity and freedom (locked doors vs open sky,
              dark rooms with a sliver of light)
            - Environments where trafficking occurs in plain sight
            - Use the VISUAL ANCHORS to ground the scene in THIS specific event,
              but the emotional focus must be on the human cost, not legal process

            TRAFFICKING VISUAL LANGUAGE (use at least 2 of these in every image):
            - Confinement imagery: locked doors, barred windows, narrow corridors, fences
            - Identity theft: scattered passports, blank IDs, confiscated documents
            - Hidden victims: eyes peering through blinds, silhouette in a dark room,
              handprints on foggy glass, a figure behind frosted window
            - Everyday disguise: neon city lights hiding dark alleys, ordinary apartment
              buildings concealing exploitation, a normal-looking storefront at night
            - Hope and resistance: an outstretched hand, a corridor leading to light,
              a broken chain, an open door at the end of a dark hallway
            - Systemic scale: rows of identical beds, assembly lines, stacked containers

            CAMERA: Real photography — focal length, aperture, angle, distance.
            Photojournalism meets fine art.

            ATMOSPHERE: One environmental effect (dust, fog, light rays, condensation)
            that adds cinematic drama and is consistent with the event's setting.

            COMPOSITION: Leave the BOTTOM 25% of the frame relatively dark or uncluttered
            so that text can be overlaid later. Think of it like a magazine cover layout zone.

            SAFETY RULES (absolute):
            - Human figures ARE allowed — but must be COMPLETELY ANONYMOUS
            - ALL faces must be: turned away, in silhouette, in deep shadow,
              heavily motion-blurred, or cropped out of frame
            - NO identifiable real individuals: no public figures, politicians,
              celebrities, activists, or named persons — not even stylized
            - NO children or minors in any form
            - NO depictions of active violence, sexual content, or graphic injury
            - NO imagery that portrays victims in a degrading or exploitative way
            - Minimal incidental text on objects (passports, signs) is OK;
              do NOT add large headlines or captions
            - When in doubt, prefer symbolic objects over human figures

            OUTPUT: Return ONLY the final image prompt as one dense paragraph describing:
            the scene/environment, the emotional core, human figures, camera and lighting,
            atmosphere, trafficking visual language elements, and the dark lower composition
            zone. Pure photography, no text.
            """
        )

        # Build optional user guidance block
        user_guidance_block = ""
        if user_guidance:
            user_guidance_block = f"USER CREATIVE DIRECTION (incorporate this into the scene):\n{user_guidance}"

        chain = prompt_maker | self.llm
        image_prompt = chain.invoke({
            "text": post_text,
            "topic": trend_topic,
            "context": trend_context,
            "visual_style": visual_style,
            "visual_elements": visual_elements,
            "user_guidance_block": user_guidance_block,
        }).content

        feedback = state.get("image_feedback")
        if feedback:
            image_prompt += f"\nCRITICAL INSTRUCTION FROM USER FOR REGENERATION: {feedback}"

        print(f"Generated Image Prompt: {image_prompt}")

        # ── 1b. Extract text overlay content via LLM ───────────────────────
        print("--- IMAGE GENERATOR: Extracting overlay text from event ---")
        from langchain_core.messages import SystemMessage, HumanMessage

        overlay: OverlayText = self.text_extractor.invoke([
            SystemMessage(content=(
                "Extract the following from the news event for a poster overlay. "
                "Keep headline under 8 words. Key fact must be a specific number, date, or data point. "
                "Source line is a short attribution."
            )),
            HumanMessage(content=f"Headline: {trend_topic}\nContext: {trend_context}\nPost: {post_text}")
        ])

        overlay_text = {
            "headline": overlay.headline,
            "key_fact": overlay.key_fact,
            "source_line": overlay.source_line,
        }
        print(f"Overlay Text: {overlay_text}")

        # ── 2. Generate Image via Gemini (with safety-filter retry) ────────
        print("--- IMAGE GENERATOR: Phase 1 — Calling Gemini API ---")

        try:
            # Attempt 1: use the full cinematic prompt
            image_part, block_reason = self._call_gemini(image_prompt)

            # Attempt 2: if blocked by safety, retry with a softened prompt
            if image_part is None and "SAFETY" in (block_reason or "").upper():
                print("--- IMAGE GENERATOR: Safety-blocked — retrying with softened prompt ---")
                softened_prompt = self._soften_prompt(image_prompt, trend_topic)
                print(f"Softened Prompt: {softened_prompt[:200]}...")
                image_part, block_reason = self._call_gemini(softened_prompt)
                image_prompt = softened_prompt  # record what was actually used

            # Still no image after retry
            if image_part is None:
                print(f"ERROR: Gemini returned no image after retry. Reason: {block_reason}")
                return {
                    "image_prompt": image_prompt,
                    "image_path": None,
                    "status": "error",
                    "feedback": f"Image generation was blocked by safety filters ({block_reason}). Try rephrasing the topic or softening the visual prompt."
                }

            generated_image_part = image_part

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.getenv("OUTPUT_DIR", "outputs")
            os.makedirs(output_dir, exist_ok=True)

            # Save raw background
            raw_path = os.path.join(output_dir, f"raw_background_{timestamp}.png")
            if hasattr(generated_image_part, 'inline_data') and generated_image_part.inline_data:
                with open(raw_path, 'wb') as f:
                    f.write(generated_image_part.inline_data.data)
            else:
                print(f"ERROR: Unrecognized format for image part: {generated_image_part}")
                return {"image_prompt": image_prompt, "image_path": None, "status": "error"}

            print(f"Raw background saved to {raw_path}")

            # ── Phase 2: Composite text overlay ────────────────────────────
            print("--- IMAGE GENERATOR: Phase 2 — Compositing text overlay ---")
            final_path = os.path.join(output_dir, f"generated_image_{timestamp}.png")
            self._composite_text_overlay(raw_path, final_path, overlay_text, visual_style)

            print(f"Final image saved to {final_path}")

            return {
                "image_prompt": image_prompt,
                "image_path": final_path,
                "overlay_text": overlay_text,
                "status": "approving_image"
            }
        except Exception as e:
            print(f"ERROR: Image Generation Failed: {e}")
            return {
                "image_prompt": image_prompt,
                "image_path": None,
                "status": "error"
            }

    # ------------------------------------------------------------------
    # Gemini API call helper (single attempt)
    # ------------------------------------------------------------------
    def _call_gemini(self, prompt: str):
        """
        Make a single Gemini image-generation call.
        Returns (image_part, block_reason).
        image_part is the generated image Part, or None if blocked/failed.
        block_reason is a string describing why it was blocked, or None on success.
        """
        try:
            result = self.genai_client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio="4:5",
                        image_size="1K",
                    )
                )
            )

            # Check if the response contains image data
            if (result.candidates
                    and result.candidates[0].content
                    and result.candidates[0].content.parts):
                return result.candidates[0].content.parts[0], None

            # Blocked — extract reason
            block_reason = "Unknown"
            if hasattr(result, 'prompt_feedback') and result.prompt_feedback:
                block_reason = str(result.prompt_feedback)
            elif result.candidates:
                candidate = result.candidates[0]
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason:
                    block_reason = str(candidate.finish_reason)
            print(f"  Gemini blocked image. Reason: {block_reason}")
            return None, block_reason

        except Exception as e:
            print(f"  Gemini API error: {e}")
            return None, str(e)

    # ------------------------------------------------------------------
    # Prompt softening for safety-filter retries
    # ------------------------------------------------------------------
    def _soften_prompt(self, original_prompt: str, topic: str) -> str:
        """
        Rewrite a blocked prompt into a symbolic, abstract version that
        avoids safety triggers while preserving the campaign's visual intent.
        Uses the LLM to intelligently rephrase.
        """
        softener = ChatPromptTemplate.from_template(
            """You are a photography director. A previous image prompt was BLOCKED
by an AI safety filter. Rewrite it into a version that will pass content
moderation while still being visually powerful for a Human Trafficking
Awareness campaign.

ORIGINAL PROMPT (blocked):
{original_prompt}

NEWS TOPIC:
{topic}

RULES FOR THE REWRITE:
1. REMOVE all depictions of: victims in distress, exploitation scenes,
   people in confinement, dark alleys with anxious figures, smuggling
   scenarios, or any scene that could be interpreted as depicting a crime
   in progress.
2. SHIFT to symbolic and metaphorical imagery:
   - A broken chain on a sunlit surface
   - An open door at the end of a bright corridor
   - Hands reaching toward light
   - A single candle illuminating darkness
   - Empty shoes or personal belongings symbolizing absence
   - A road leading from shadow into light
   - Documentary-style cityscape at dawn (hope, new beginning)
3. Keep it as ONE dense paragraph describing a photograph.
4. Maintain cinematic quality: specify camera, lighting, atmosphere.
5. Keep the BOTTOM 25% dark/uncluttered for text overlay.
6. NO people in distress. Silhouettes and distant anonymous figures are OK.
7. NO text, headlines, or captions in the scene.
8. ALL human figures must be anonymous: backs of heads, silhouettes,
   or hands only. No identifiable faces or named individuals.
9. NO real public figures, politicians, or celebrities in any form.

OUTPUT: Return ONLY the rewritten prompt. One paragraph."""
        )

        chain = softener | self.llm
        softened = chain.invoke({
            "original_prompt": original_prompt,
            "topic": topic,
        }).content

        return softened


    def _composite_text_overlay(
        self,
        background_path: str,
        output_path: str,
        overlay_text: dict,
        visual_style: str = ""
    ):
        """
        Composites headline, key fact, and source onto the background image
        in a National Geographic editorial poster style.
        """
        img = Image.open(background_path).convert("RGBA")
        w, h = img.size

        # ── Color theme from visual style ──────────────────────────────
        accent_color = self._pick_accent_color(visual_style)
        text_color = (255, 255, 255)         # White body text
        shadow_color = (0, 0, 0, 200)        # Text shadow

        # ── Load fonts (National Geographic editorial style) ───────────
        # Headline: large serif (Playfair Display — similar to NG editorial)
        # Key fact: medium sans-serif bold
        # Source:   small sans-serif
        headline_size = max(int(h * 0.055), 28)
        fact_size = max(int(h * 0.035), 18)
        source_size = max(int(h * 0.022), 13)

        font_headline = _load_font("PlayfairDisplay[wght].ttf", headline_size)
        font_fact = _load_font("Roboto[wdth,wght].ttf", fact_size)
        font_source = _load_font("Roboto[wdth,wght].ttf", source_size)

        # ── Create overlay layer ───────────────────────────────────────
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # ── Bottom gradient mask (National Geographic style) ───────────
        # Smooth gradient from transparent to dark, covering bottom ~40%
        gradient_start = int(h * 0.55)
        for y in range(gradient_start, h):
            progress = (y - gradient_start) / (h - gradient_start)
            # Ease-in curve for more natural gradient
            alpha = int(210 * (progress ** 1.5))
            draw.rectangle([(0, y), (w, y + 1)], fill=(0, 0, 0, alpha))

        # ── Yellow accent bar — will be drawn after text layout is computed ──
        bar_height = max(int(h * 0.005), 3)
        bar_margin = int(w * 0.06)

        # ── Text layout (bottom-up to prevent overlap) ─────────────────
        margin = int(w * 0.06)
        max_text_width = w - 2 * margin
        spacing = int(h * 0.015)

        # 1. Source line — anchored at the very bottom
        source_line = overlay_text.get("source_line", "")
        source_y = h - int(h * 0.035)
        draw.text(
            (margin, source_y),
            source_line,
            font=font_source,
            fill=(200, 200, 200, 220)
        )

        # 2. Key fact — above source line
        key_fact = overlay_text.get("key_fact", "")
        fact_lines = self._wrap_text(key_fact, font_fact, max_text_width, draw)
        fact_height = len(fact_lines) * (fact_size + 4)
        fact_y = source_y - fact_height - spacing
        self._draw_text_with_shadow(
            draw, key_fact, font_fact, accent_color, shadow_color,
            margin, fact_y, max_text_width
        )

        # 3. Headline — above key fact
        headline = overlay_text.get("headline", "").upper()
        headline_lines = self._wrap_text(headline, font_headline, max_text_width, draw)
        headline_height = len(headline_lines) * (headline_size + 4)
        headline_y = fact_y - headline_height - spacing
        self._draw_text_with_shadow(
            draw, headline, font_headline, text_color, shadow_color,
            margin, headline_y, max_text_width
        )

        # 4. Yellow accent bar — just above the headline
        bar_y = headline_y - int(h * 0.015) - bar_height
        draw.rectangle(
            [(bar_margin, bar_y), (w - bar_margin, bar_y + bar_height)],
            fill=accent_color
        )

        # ── Merge overlay onto background ──────────────────────────────
        composite = Image.alpha_composite(img, overlay)
        composite = composite.convert("RGB")
        composite.save(output_path, quality=95)

    def _draw_text_with_shadow(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        color: tuple,
        shadow_color: tuple,
        x: int,
        y: int,
        max_width: int,
    ):
        """Draw wrapped text with a drop shadow for readability."""
        lines = self._wrap_text(text, font, max_width, draw)
        line_height = font.size + 4

        for i, line in enumerate(lines):
            ly = y + i * line_height
            # Shadow (offset by 2px)
            draw.text((x + 2, ly + 2), line, font=font, fill=shadow_color)
            # Main text
            draw.text((x, ly), line, font=font, fill=color)

    @staticmethod
    def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
        """Word-wrap text to fit within max_width pixels."""
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines or [""]

    @staticmethod
    def _pick_accent_color(visual_style: str) -> tuple:
        """
        Choose an accent color based on the audience's visual style brief.
        Returns RGBA tuple.
        """
        style_lower = visual_style.lower()

        if "neon" in style_lower or "vibrant" in style_lower:
            return (0, 255, 170, 255)     # Neon green (college_students)
        elif "corporate" in style_lower or "blue-steel" in style_lower:
            return (100, 180, 255, 255)   # Corporate blue (business_owners)
        elif "warm" in style_lower and "amber" in style_lower:
            return (255, 200, 80, 255)    # Warm amber (parents)
        elif "desaturated" in style_lower or "documentary" in style_lower:
            return (200, 200, 200, 255)   # Muted silver (lawmakers)
        elif "portra" in style_lower or "cream" in style_lower:
            return (230, 180, 100, 255)   # Warm gold (educators)
        else:
            # Default: National Geographic signature yellow
            return (255, 200, 0, 255)
