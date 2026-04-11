# Image Prompting Pipeline — How It Works

This document explains how the system constructs the image generation prompt, where each `{}` parameter comes from, and how they flow through the multi-agent pipeline.

---

## The Prompt Template

The core prompt lives in `image_generator.py` and is a `ChatPromptTemplate` with **5 dynamic parameters**:

```
{topic}        — Trend headline
{context}      — Detailed news context
{text}         — The written post text
{visual_style} — Art direction brief from audience analysis
{visual_elements} — Event-specific visual anchors
```

These are injected into a photography-director system prompt that instructs GPT-4o-mini to produce a single dense paragraph describing a cinematic, text-free photograph for the Gemini image model.

---

## How Each `{}` Parameter Is Derived

### 1. `{topic}` — from `TrendAnalyzerAgent`

**State key:** `trend_topic`

The `TrendAnalyzerAgent` queries the Exa API for real-time human trafficking news. It uses GPT-4o-mini to select the most impactful story and outputs a concise headline string.

```
Exa API (live news) → GPT-4o-mini (selection) → trend_topic
```

### 2. `{context}` — from `TrendAnalyzerAgent`

**State key:** `trend_context`

Same agent, same LLM call. The model produces a multi-paragraph context summary alongside the topic — covering who, what, where, and key facts.

```
Exa API (live news) → GPT-4o-mini (summarization) → trend_context
```

### 3. `{text}` — from `WriterAgent`

**State key:** `post_text`

The `WriterAgent` receives `trend_topic`, `trend_context`, and `audience_brief` (see below). It drafts a social-media post tailored to the selected audience's tone and CTA style.

```
trend_topic + trend_context + audience_brief → GPT-4o-mini → post_text
```

### 4. `{visual_style}` — from `AudienceAnalyzer`

**State key:** `visual_style`

The `AudienceAnalyzer` matches the news story to one of 6 predefined audience profiles in `config/audience_profiles.md`. Each profile includes a **Visual Style** section defining:

- Color palette (e.g. "neon accents on dark background", "corporate blue-steel")
- Lighting mood (e.g. "dramatic chiaroscuro", "soft window light")
- Setting/environment (e.g. "gritty urban", "home environment")
- Texture (e.g. "street-art / graffiti", "Kodak Portra warmth")
- Typography style (e.g. "bold chunky sans-serif", "clean Helvetica")

The LLM reads the profiles table and outputs a complete visual style brief string.

```
trend_topic + trend_context + audience_profiles.md → GPT-4o-mini → visual_style
```

**This also determines the accent color** used in Phase 2 text compositing via `_pick_accent_color()`, which pattern-matches keywords in the style string:

| Keyword in `visual_style` | Accent Color |
|---|---|
| "neon" / "vibrant" | Neon green `(0,255,170)` |
| "corporate" / "blue-steel" | Corporate blue `(100,180,255)` |
| "warm" + "amber" | Warm amber `(255,200,80)` |
| "desaturated" / "documentary" | Muted silver `(200,200,200)` |
| "portra" / "cream" | Warm gold `(230,180,100)` |
| *(default)* | NatGeo yellow `(255,200,0)` |

### 5. `{visual_elements}` — from `AudienceAnalyzer`

**State key:** `visual_elements`

In the same LLM call that produces `visual_style`, the `AudienceAnalyzer` also extracts **2–3 concrete visual scenes** grounded in the actual news event. These are the mandatory "visual anchors" the image prompt must incorporate.

The structured output schema enforces that at least one element shows the **human dimension** of trafficking (victim environment, exploitation conditions, intervention moments), not just legal/courtroom imagery.

```
trend_topic + trend_context + audience_profiles.md → GPT-4o-mini → visual_elements
```

**Example output:**
> "migrant workers crammed in a dimly lit factory dormitory, a row of confiscated passports spread on a steel table, the neon glow of a massage parlor at night on a rainy street"

---

## End-to-End Data Flow

```
┌─────────────────┐
│ TrendAnalyzer   │──→ trend_topic ──────────→ {topic}
│ (Exa + GPT-4o)  │──→ trend_context ────────→ {context}
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│AudienceAnalyzer │──→ visual_style ─────────→ {visual_style}
│ (GPT-4o-mini)   │──→ visual_elements ──────→ {visual_elements}
│                 │──→ audience_brief ────┐
└────────┬────────┘                      │
         │                               ▼
         │                    ┌─────────────────┐
         │                    │   Writer        │
         │                    │  (GPT-4o-mini)  │──→ post_text → {text}
         │                    └─────────────────┘
         ▼
┌──────────────────────────────────────────────────┐
│              ImageGeneratorAgent                 │
│                                                  │
│  Phase 1a: GPT-4o-mini builds image prompt       │
│            using {topic, context, text,          │
│            visual_style, visual_elements}        │
│                                                  │
│  Phase 1b: GPT-4o-mini extracts OverlayText      │
│            (headline, key_fact, source_line)      │
│                                                  │
│  Phase 2:  Gemini generates text-free photograph │
│                                                  │
│  Phase 3:  Pillow composites text overlay onto   │
│            the image (NatGeo editorial style)    │
└──────────────────────────────────────────────────┘
```

---

## Summary

| Step | Agent | Input | Output (→ prompt param) |
|---|---|---|---|
| 1 | TrendAnalyzer | Exa API results | `trend_topic` → `{topic}` |
| 2 | TrendAnalyzer | Exa API results | `trend_context` → `{context}` |
| 3 | AudienceAnalyzer | topic + context + profiles | `visual_style` → `{visual_style}` |
| 4 | AudienceAnalyzer | topic + context + profiles | `visual_elements` → `{visual_elements}` |
| 5 | Writer | topic + context + audience_brief | `post_text` → `{text}` |
| 6 | ImageGenerator | All 5 params above | Final image prompt → Gemini API |
