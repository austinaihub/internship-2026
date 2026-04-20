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
        self._visual_philosophy = self._load_visual_philosophy()
        self._visual_styles = self._load_visual_styles()

    @staticmethod
    def _load_visual_philosophy() -> str:
        path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "visual_philosophy.md"))
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    @staticmethod
    def _load_visual_styles() -> dict:
        """Load visual_styles.md and parse into {preset_name: section_text} dict."""
        path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "visual_styles.md"))
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            return {}

        styles = {}
        current_key = None
        current_lines = []
        for line in content.split("\n"):
            if line.startswith("## ") and not line.startswith("## Visual"):
                if current_key:
                    styles[current_key] = "\n".join(current_lines).strip()
                current_key = line[3:].strip()
                current_lines = []
            elif current_key is not None:
                current_lines.append(line)
        if current_key:
            styles[current_key] = "\n".join(current_lines).strip()
        return styles

    def _get_style_preset_text(self, preset_name: str) -> str:
        """Get the full style description for a preset, with fallback."""
        return self._visual_styles.get(preset_name, self._visual_styles.get("cinematic_depth", ""))

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
        visual_style_preset = state.get("visual_style_preset") or "cinematic_depth"
        visual_elements = state.get("visual_elements") or ""
        trend_topic = state.get("trend_topic") or ""
        trend_context = state.get("trend_context") or ""
        user_guidance = state.get("user_guidance") or ""

        # Load the full style preset description
        style_preset_text = self._get_style_preset_text(visual_style_preset)
        print(f"--- IMAGE GENERATOR: Using style preset '{visual_style_preset}' ---")

        # ── 1a. Generate image prompt (photography only, NO text) ──────────
        prompt_maker = ChatPromptTemplate.from_template(
            """
            You are a minimalist photography director for a Human Trafficking Awareness campaign.

            DESIGN PHILOSOPHY:
            {visual_philosophy}

            PHOTOGRAPHY STYLE — {style_preset_name}:
            {style_preset_text}

            YOUR TASK: Create ONE image prompt following the photography style above.
            The style defines the lighting, background, composition, palette, and camera.
            You MUST follow these style rules strictly — they are non-negotiable.

            EVENT:
            Headline: {topic}
            Context: {context}

            AUDIENCE COLOR/MOOD DIRECTION: {visual_style}

            VISUAL ANCHOR (build the image around this ONE detail):
            {visual_elements}

            ADDITIONAL RULES:
            1. ONE subject only. Do not combine multiple symbols or metaphors.
            2. Bottom 25% of frame: dark or uncluttered (text overlay zone).
            3. Depict WHERE the event happened, not where it was discussed.
            4. No text, headlines, or captions in the image.

            SAFETY (absolute):
            - Human figures allowed but COMPLETELY ANONYMOUS (silhouettes, backs
              of heads, hands, deep shadow). No identifiable faces.
            - No real individuals, public figures, or named persons.
            - No children or minors.
            - No active violence, sexual content, or graphic injury.
            - No degrading depictions of victims.
            - When in doubt, choose a symbolic object over a human figure.

            OUTPUT: One dense paragraph. Describe: the single subject, its environment,
            camera angle and lens, lighting (per the style), and the negative space.
            Keep it under 120 words. Pure photography, no text.
            """
        )

        chain = prompt_maker | self.llm
        image_prompt = chain.invoke({
            "visual_philosophy": self._visual_philosophy,
            "style_preset_name": visual_style_preset,
            "style_preset_text": style_preset_text,
            "topic": trend_topic,
            "context": trend_context,
            "visual_style": visual_style,
            "visual_elements": visual_elements,
        }).content

        # Front-load user guidance (primacy bias is stronger for image gen models)
        if user_guidance:
            image_prompt = (
                f"HIGH PRIORITY — USER DIRECTIVE: {user_guidance}\n\n"
                f"{image_prompt}"
            )

        # Append rejection feedback at end (CRITICAL priority)
        feedback = state.get("image_feedback")
        if feedback:
            image_prompt += f"\nCRITICAL — USER REJECTION FEEDBACK (this MUST be addressed, non-negotiable): {feedback}"

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

            # Gemini 3 returns FinishReason.NO_IMAGE (generic refusal) or PROHIBITED_CONTENT
            # in addition to the classic SAFETY block. Treat all three as retry-worthy.
            def _is_refusal(reason: str | None) -> bool:
                r = (reason or "").upper()
                return any(k in r for k in ("SAFETY", "NO_IMAGE", "PROHIBITED", "BLOCK"))

            # Attempt 2: softened prompt
            if image_part is None and _is_refusal(block_reason):
                print(f"--- IMAGE GENERATOR: Blocked ({block_reason}) — retrying with softened prompt ---")
                softened_prompt = self._soften_prompt(image_prompt, trend_topic)
                print(f"Softened Prompt: {softened_prompt[:200]}...")
                image_part, block_reason = self._call_gemini(softened_prompt)
                image_prompt = softened_prompt

            # Attempt 3: ultra-minimal symbolic fallback (no distress cues at all)
            if image_part is None and _is_refusal(block_reason):
                print(f"--- IMAGE GENERATOR: Still blocked ({block_reason}) — falling back to minimal symbolic prompt ---")
                fallback_prompt = self._minimal_fallback_prompt(trend_topic, visual_style_preset)
                print(f"Fallback Prompt: {fallback_prompt[:200]}...")
                image_part, block_reason = self._call_gemini(fallback_prompt)
                image_prompt = fallback_prompt

            # Still no image after all retries
            if image_part is None:
                print(f"ERROR: Gemini returned no image after all retries. Reason: {block_reason}")
                return {
                    "image_prompt": image_prompt,
                    "image_path": None,
                    "status": "error",
                    "feedback": (
                        "Image generation was blocked by safety filters even after softening the prompt. "
                        "Try a less sensitive angle on the topic, or add guidance like "
                        "'use purely symbolic imagery, no human figures' in the audience step."
                    )
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
                "status": "approving_image",
                "prompt_log": [{
                    "agent": "image_generator",
                    "summary": image_prompt[:200],
                    "user_guidance": bool(user_guidance),
                    "image_feedback": bool(feedback),
                }],
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
            """A previous image prompt was BLOCKED by a safety filter. Rewrite it
as a minimalist, symbolic photograph that will pass moderation.

ORIGINAL (blocked): {original_prompt}
TOPIC: {topic}

REWRITE RULES:
1. Replace any distress/exploitation/confinement scene with ONE symbolic object
   (e.g., a single open door in light, a broken chain on concrete, an empty chair).
2. ONE subject, 50-60% negative space, 2-3 color tones. Minimalist composition.
3. No people in distress. Anonymous silhouettes OK if distant and peaceful.
4. No text/captions in the image. Bottom 25% dark for overlay.
5. Specify camera, lens, and lighting. Keep under 100 words.

OUTPUT: One paragraph, the rewritten prompt only."""
        )

        chain = softener | self.llm
        softened = chain.invoke({
            "original_prompt": original_prompt,
            "topic": topic,
        }).content

        return softened

    # ------------------------------------------------------------------
    # Ultra-minimal fallback when even softening gets blocked
    # ------------------------------------------------------------------
    def _minimal_fallback_prompt(self, topic: str, style_preset: str = "editorial_flat") -> str:
        """
        Last-resort prompt: no people, no distress cues, no topic-specific
        imagery. Just a symbolic still-life that Gemini will almost always
        render. We keep the overlay text system to carry the message.
        """
        # Pick neutral symbolic objects — no human subjects at all
        symbols = [
            "a single open wooden door at the end of a softly lit corridor",
            "one empty wooden chair in a quiet room, morning light through a window",
            "a broken metal chain resting on weathered concrete",
            "a small paper boat on still water under diffused grey sky",
            "a single candle flame in near-darkness, surrounded by negative space",
        ]
        import random
        symbol = random.choice(symbols)

        return (
            f"Minimalist editorial still-life photograph: {symbol}. "
            f"50mm lens, shallow depth of field, muted desaturated palette of "
            f"deep navy, warm cream, and soft amber. 60% negative space. "
            f"Bottom 30% of frame is dark for text overlay. "
            f"No people, no text, no words, no letters in the image. "
            f"Quiet, contemplative, editorial tone. Shot for a National Geographic-style poster."
        )


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
