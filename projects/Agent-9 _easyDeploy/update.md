# Agent-9 Technical Deep Dive

> **Three core systems explained:** How news is discovered via keywords, how campaign images are generated from raw material to final composite, and how Human-in-the-Loop ensures user intent always takes priority.

---

## Table of Contents

- [Part 1: Keyword System & News Search Pipeline](#part-1-keyword-system--news-search-pipeline)
  - [1.1 Pipeline Overview](#11-pipeline-overview)
  - [1.2 The Query Pool (12 Queries × 4 Dimensions)](#12-the-query-pool-12-queries--4-dimensions)
  - [1.3 Query Selection Logic](#13-query-selection-logic)
  - [1.4 Exa Neural Search Execution](#14-exa-neural-search-execution)
  - [1.5 GPT-4o Topic Extraction & Dedup](#15-gpt-4o-topic-extraction--dedup)
  - [1.6 HITL: Human Trend Review](#16-hitl-human-trend-review)
- [Part 2: Image Generation Pipeline](#part-2-image-generation-pipeline)
  - [2.1 End-to-End Overview](#21-end-to-end-overview)
  - [2.2 Stage 1: Audience & Material Analysis](#22-stage-1-audience--material-analysis)
  - [2.3 Stage 2: Prompt Composition](#23-stage-2-prompt-composition--how-visual-style-becomes-a-camera-prompt)
  - [2.4 Stage 2b: Overlay Text Extraction](#24-stage-2b-overlay-text-extraction)
  - [2.5 Stage 3: Gemini Image Generation](#25-stage-3-gemini-image-generation)
  - [2.6 Stage 4: Pillow Text Compositing](#26-stage-4-pillow-text-compositing)
  - [2.7 Design Principles: Visual Philosophy](#27-design-principles-visual-philosophy)
- [Part 3: Human-in-the-Loop (HITL) System](#part-3-human-in-the-loop-hitl-system)
  - [3.1 HITL Checkpoint Map](#31-hitl-checkpoint-map)
  - [3.2 Checkpoint 1: Trend Review](#32-checkpoint-1-trend-review)
  - [3.3 Checkpoint 2: Content Review](#33-checkpoint-2-content-review)
  - [3.4 Checkpoint 3: Post-Publish Refinement](#34-checkpoint-3-post-publish-refinement)
  - [3.5 User Input Priority: How Code Ensures User Intent Wins](#35-user-input-priority-how-code-ensures-user-intent-wins)
  - [3.6 Priority Propagation: One Input, Four Agents](#36-priority-propagation-one-input-four-agents)
- [Technology Stack Reference](#technology-stack-reference)

---

# Part 1: Keyword System & News Search Pipeline

## 1.1 Pipeline Overview

```mermaid
flowchart LR
    A["🔑 Keywords\nSelection"] --> B["🔍 Exa Neural\nSearch"]
    B --> C["🧠 GPT-4o\nTopic Extraction"]
    C --> D["👤 HITL\nTrend Review"]

    style A fill:#6c5ce7,color:#fff,stroke:none
    style B fill:#0984e3,color:#fff,stroke:none
    style C fill:#00b894,color:#fff,stroke:none
    style D fill:#fdcb6e,color:#000,stroke:none
```

**Data flow:** `12 predefined queries` → `2 selected per run` → `Exa search across 13 domains` → `GPT-4o picks single best story` → `User approves / re-searches`

## 1.2 The Query Pool (12 Queries × 4 Dimensions)

The system maintains **12 natural-language queries** in `src/agents/trend_analyzer.py`, balanced across 4 dimensions:

```mermaid
pie title Query Pool Distribution
    "Law Enforcement & Prosecution" : 3
    "Policy & Legislation" : 2
    "Industry & Labor Exploitation" : 3
    "Tech, Prevention & Survivors" : 4
```

| Dimension | Count | Example Query |
|-----------|:-----:|---------------|
| **Law Enforcement** | 3 | `"human trafficking conviction sentencing court ruling this week"` |
| **Policy & Legislation** | 2 | `"new anti-trafficking law or bill passed in any country"` |
| **Industry & Labor** | 3 | `"forced labor in agriculture construction hospitality or fishing exposed"` |
| **Tech / Prevention / Survivors** | 4 | `"technology or AI tools used to detect or combat human trafficking"` |

> **Why natural language?** The downstream search engine (**Exa**) uses `type="neural"` — a semantic embedding-based search. Full intent sentences outperform keyword fragments.

## 1.3 Query Selection Logic

```mermaid
flowchart TD
    START["User starts campaign"] --> CHECK{"User provided\nkeywords?"}
    CHECK -->|Yes| PATH_A["selected = [user_keywords,\nrandom.choice(pool)]"]
    CHECK -->|No| PATH_B["selected = random.sample(pool, k=2)"]
    PATH_A --> EXEC["Execute 2 queries\nvia Exa"]
    PATH_B --> EXEC

    style START fill:#dfe6e9,color:#2d3436,stroke:#b2bec3
    style CHECK fill:#ffeaa7,color:#2d3436,stroke:#fdcb6e
    style PATH_A fill:#55efc4,color:#2d3436,stroke:#00b894
    style PATH_B fill:#74b9ff,color:#2d3436,stroke:#0984e3
    style EXEC fill:#a29bfe,color:#fff,stroke:#6c5ce7
```

- **With user keywords:** User's input = Query 1; `random.choice()` from pool = Query 2 — guarantees intent + serendipity.
- **Without keywords:** `random.sample(pool, k=2)` — two non-repeating queries for maximum diversity.

## 1.4 Exa Neural Search Execution

Each query is searched across **13 trusted domains** defined in `config.py`:

```mermaid
flowchart LR
    subgraph Authorities["🏛️ Authority Sources (7)"]
        A1["unodc.org"]
        A2["polarisproject.org"]
        A3["hrw.org"]
        A4["ijm.org"]
        A5["ilo.org"]
        A6["thorn.org"]
        A7["ctdatacollaborative.org"]
    end

    subgraph News["📰 Global News (6)"]
        N1["reuters.com"]
        N2["apnews.com"]
        N3["theguardian.com"]
        N4["bbc.com"]
        N5["cnn.com"]
        N6["aljazeera.com"]
    end

    Q["Each Query"] --> Authorities
    Q --> News
```

**Per-query execution detail:**

```python
# For each of 2 queries × 13 domains:
Exa.search_and_contents(
    query,
    type        = "neural",        # Semantic search
    category    = "news",          # News-only filter
    start_date  = 7_days_ago,      # Recency window
    include_domains = [domain],    # One domain at a time
    num_results = 3,               # Top 3 per domain
    text        = True             # Include full article text
)
```

**Theoretical max:** `2 × 13 × 3 = 78 articles` (typically 10–30 after dedup and empty-result filtering).

**Reliability layer** (`@reliable_news_tool` decorator):
- `max_retries=3` with exponential backoff (`2^attempt` seconds)
- 30-second timeout per call
- **Crawl4AI** fallback: if Exa returns metadata but `content < 50 chars`, the scraper fetches full article text

## 1.5 GPT-4o Topic Extraction & Dedup

```mermaid
flowchart TD
    ARTICLES["All retrieved articles\n(each truncated to 1500 chars)"] --> LLM
    DEDUP["used_topics.json\n(rolling 30 topics)"] --> LLM
    LLM["GPT-4o\n(temperature=0)"] --> OUT

    OUT["TrendAnalysis {\n  topic: str\n  context: str\n  used_source_urls: List[str]\n}"]

    OUT --> SAVE["Append to\nused_topics.json"]

    style LLM fill:#00b894,color:#fff,stroke:none
    style OUT fill:#dfe6e9,color:#2d3436,stroke:#b2bec3
    style DEDUP fill:#fdcb6e,color:#2d3436,stroke:none
```

**Rules enforced in prompt:**
- ✅ ONLY human trafficking stories (sex trafficking, labor trafficking, debt bondage)
- ❌ Reject: drug trafficking, general immigration, unrelated human rights
- ✅ Pick highest law-enforcement or legislative impact
- ✅ Dedup: previously used topics injected as "ALREADY COVERED — do NOT pick again"

**Structured output:** Uses `PydanticOutputParser` with `TrendAnalysis` schema — guarantees typed, parseable output.

## 1.6 HITL: Human Trend Review

After topic extraction, the pipeline pauses at `status: "approving_trend"`. The user can:

| Action | Effect |
|--------|--------|
| **Approve** AI recommendation | Continue with extracted topic |
| **Select different article** | Override topic with a specific article from `all_retrieved_news` |
| **Type custom topic** | Override with free-text input (takes priority) |
| **Add creative guidance** | Text propagates to Audience Analyzer, Writer, and Image Generator |
| **Re-search** | Triggers fresh `random.sample()` + Exa search cycle |

---

# Part 2: Image Generation Pipeline

## 2.1 End-to-End Overview

```mermaid
flowchart LR
    subgraph Stage1["Stage 1: Analysis"]
        AA["Audience\nAnalyzer\n─────────\nGPT-4o-mini"]
    end

    subgraph Stage2["Stage 2: Prompt"]
        PC["Prompt\nComposer\n─────────\nGPT-4o-mini"]
        TE["Text\nExtractor\n─────────\nGPT-4o-mini"]
    end

    subgraph Stage3["Stage 3: Generation"]
        GEM["Gemini 3.1\nFlash\n─────────\n4:5 · 1K"]
    end

    subgraph Stage4["Stage 4: Composite"]
        PIL["Pillow\n(PIL)\n─────────\nPython"]
    end

    AA -->|"visual_style\nvisual_anchor"| PC
    AA -->|"audience_brief"| WRITER["Writer\nAgent"]
    PC -->|"~100 word\nprompt"| GEM
    TE -->|"headline\nkey_fact\nsource"| PIL
    GEM -->|"raw_background\n.png"| PIL
    PIL -->|"final_image\n.png"| HITL["👤 HITL\nReview"]

    style AA fill:#f0932b,color:#fff,stroke:none
    style PC fill:#e17055,color:#fff,stroke:none
    style TE fill:#e17055,color:#fff,stroke:none
    style GEM fill:#d63031,color:#fff,stroke:none
    style PIL fill:#6c5ce7,color:#fff,stroke:none
    style HITL fill:#fdcb6e,color:#000,stroke:none
    style WRITER fill:#be2edd,color:#fff,stroke:none
```

## 2.2 Stage 1: Audience & Material Analysis

**Agent:** `AudienceAnalyzer` · **Model:** `GPT-4o-mini` (`temperature=0`) · **Output:** `Pydantic` structured

```mermaid
flowchart TD
    IN1["trend_topic\n+ trend_context"] --> AA
    IN2["audience_profiles.md\n(6 profiles)"] --> AA
    IN3["user_guidance\n(optional)"] --> AA

    AA["AudienceAnalyzer\nGPT-4o-mini"] --> OUT

    OUT["AudienceDecision {\n  target_audience: str\n  audience_brief: str\n  visual_style: str      // ≤25 words\n  visual_elements: str   // ONE anchor\n  reasoning: str\n}"]

    style AA fill:#f0932b,color:#fff,stroke:none
    style OUT fill:#dfe6e9,color:#2d3436,stroke:#b2bec3
```

### The 6 Audience Profiles (with Anti-keywords)

Each profile in `config/audience_profiles.md` includes **Trigger Keywords** for matching AND **Anti-keywords** to prevent near-miss collisions:

| Audience | Trigger Signals | Anti-signals |
|----------|----------------|--------------|
| `college_students` | campus, sextortion, dating app, peer recruitment | NOT supply chain, NOT legislative policy |
| `educators` | school, K-12, curriculum, mandatory reporting | NOT parental tools, NOT university-age |
| `business_owners` | supply chain, forced labor, ESG, agriculture, construction, fishing | NOT online/sexual, NOT school-based |
| `parents` | grooming, teen, parental control, online safety | NOT school policy, NOT college-age |
| `lawmakers` | legislation, bill, federal, treaty, prosecution reform | ONLY if clear policy dimension |
| `general_public` | *(default fallback)* | *(catch-all)* |

### Key Outputs That Drive Image Generation

| Output | Size | Example | Used By |
|--------|------|---------|---------|
| `visual_style` | ~20 words | *"Cool blue-steel tones, tungsten lighting, authoritative and restrained"* | Image prompt + accent color picker |
| `visual_elements` | 1 sentence | *"A row of confiscated passports on a cold steel table"* | Image prompt (single visual anchor) |
| `audience_brief` | 2-3 sentences | *"Business-oriented, compliance-focused. Frame as legal liability..."* | Writer Agent |

## 2.3 Stage 2: Prompt Composition — How Visual Style Becomes a Camera Prompt

**Agent:** `ImageGeneratorAgent.llm` · **Model:** `GPT-4o-mini` (`temperature=0.7`) · **Output limit:** ≤120 words

```mermaid
flowchart TD
    VP["visual_philosophy.md\n(design rules)"] --> LLM
    VS["visual_style\n(~20 words from Audience)"] --> LLM
    VE["visual_elements\n(1 anchor sentence)"] --> LLM
    TC["trend_topic\n+ trend_context"] --> LLM
    UG["user_guidance\n(optional)"] --> LLM

    LLM["GPT-4o-mini\n(temperature=0.7)"] --> PROMPT

    PROMPT["Image Prompt\n≤120 words\n──────────────\nSingle subject\nCamera + lens\nLighting\nNegative space\nColor tones"]

    style LLM fill:#e17055,color:#fff,stroke:none
    style VP fill:#81ecec,color:#2d3436,stroke:none
    style PROMPT fill:#dfe6e9,color:#2d3436,stroke:#b2bec3
```

### Rules Enforced in the Prompt Template

| Rule | What it means |
|------|---------------|
| **ONE subject only** | No combined symbols. A passport OR a silhouette — not both. |
| **50-60% negative space** | Frame is mostly blur, shadow, sky, or gradient. |
| **Shallow depth of field** | Sharp subject, soft everything else. |
| **2-3 color tones max** | Restrained palette. Monochrome often wins. |
| **Bottom 25% dark** | Reserved for text overlay — also grounds composition. |
| **Depict the event** | Show WHERE it happened, not WHERE it was discussed. |
| **No text in image** | No headlines, captions, or decorative text rendered by AI. |

### Safety Rules (Hard-coded, Never Removed)

- All human figures → **completely anonymous** (silhouettes, backs of heads, hands, deep shadow)
- No identifiable real individuals, public figures, or named persons
- No children or minors in any form
- No active violence, sexual content, or graphic injury
- No degrading depictions of victims
- When in doubt → symbolic object over human figure

## 2.4 Stage 2b: Overlay Text Extraction

Runs in parallel with prompt composition. A separate `GPT-4o-mini` call (`temperature=0`) extracts poster overlay content:

```
OverlayText {
    headline:    str   // ≤8 words, punchy         → "JUSTICE SERVED IN TEXAS"
    key_fact:    str   // Specific data point       → "3 convicted, $2.4M seized"
    source_line: str   // Short attribution         → "Source: Reuters"
}
```

## 2.5 Stage 3: Gemini Image Generation

**API:** `Google Gemini 3.1 Flash (Image Preview)` · **Aspect:** `4:5` · **Resolution:** `1K`

```mermaid
flowchart TD
    PROMPT["Image prompt\n(≤120 words)"] --> ATT1

    ATT1["Attempt 1:\nFull prompt → Gemini"] --> CHECK{"Image\nreturned?"}

    CHECK -->|"✅ Yes"| SAVE["raw_background.png\nsaved to outputs/"]
    CHECK -->|"❌ Safety\nblocked"| SOFTEN

    SOFTEN["_soften_prompt()\nGPT-4o-mini rewrites\nto symbolic/abstract"] --> ATT2

    ATT2["Attempt 2:\nSoftened prompt → Gemini"] --> CHECK2{"Image\nreturned?"}

    CHECK2 -->|"✅ Yes"| SAVE
    CHECK2 -->|"❌ Still blocked"| ERR["Return error\nto user"]

    style ATT1 fill:#d63031,color:#fff,stroke:none
    style ATT2 fill:#e17055,color:#fff,stroke:none
    style SOFTEN fill:#fdcb6e,color:#2d3436,stroke:none
    style SAVE fill:#00b894,color:#fff,stroke:none
    style ERR fill:#636e72,color:#fff,stroke:none
```

**Safety-filter retry:** If Gemini blocks the original prompt, `_soften_prompt()` uses GPT-4o-mini to rewrite it — replacing confinement scenes with symbolic imagery (e.g., *"a single open door in light"*, *"a broken chain on sunlit concrete"*) while preserving minimalist composition rules.

## 2.6 Stage 4: Pillow Text Compositing

**Library:** `Pillow (PIL)` · **No LLM** — pure Python image processing

```mermaid
flowchart TD
    BG["raw_background.png\n(from Gemini)"] --> GRAD

    GRAD["Layer 1:\nBottom Gradient Mask\n─────────────────\nCovers bottom ~45%\nTransparent → Black\nalpha = 210 × progress^1.5"] --> TEXT

    TEXT["Layer 2:\nText Elements\n─────────────────\n(laid out bottom-up)"] --> MERGE

    subgraph TEXT_DETAIL["Text Layout (bottom → top)"]
        SRC["④ Source Line\nRoboto · 2.2% height\nLight gray"]
        FACT["③ Key Fact\nRoboto · 3.5% height\nAccent color"]
        HEAD["② Headline\nPlayfair Display · 5.5% height\nWhite · UPPERCASE"]
        BAR["① Accent Bar\nAudience-matched color"]
    end

    MERGE["Image.alpha_composite()\n→ final_image.png"]

    style GRAD fill:#636e72,color:#fff,stroke:none
    style TEXT fill:#6c5ce7,color:#fff,stroke:none
    style MERGE fill:#00b894,color:#fff,stroke:none
```

### Accent Color Selection

The accent color (used for **key fact text** and **accent bar**) is determined by keyword matching against `visual_style`:

| `visual_style` contains | Color | RGB | Audience |
|--------------------------|-------|-----|----------|
| `"neon"` or `"vibrant"` | 🟢 Neon green | `(0, 255, 170)` | college_students |
| `"blue-steel"` | 🔵 Corporate blue | `(100, 180, 255)` | business_owners |
| `"warm"` + `"amber"` | 🟡 Warm amber | `(255, 200, 80)` | parents |
| `"desaturated"` | ⚪ Muted silver | `(200, 200, 200)` | lawmakers |
| `"cream"` | 🟤 Warm gold | `(230, 180, 100)` | educators |
| *(default)* | 🟡 NG Yellow | `(255, 200, 0)` | general_public |

### Font Stack & Fallback

| Element | Primary Font | Fallback |
|---------|-------------|----------|
| Headline | `PlayfairDisplay[wght].ttf` (serif) | → `arial.ttf` → PIL default |
| Key Fact | `Roboto[wdth,wght].ttf` (sans-serif) | → `arial.ttf` → PIL default |
| Source | `Roboto[wdth,wght].ttf` (sans-serif) | → `arial.ttf` → PIL default |

Fonts bundled in `config/fonts/`. `_load_font()` provides graceful fallback.

### Text Layout Algorithm (Bottom-Up)

```
  Position                  Element                  Sizing
  ───────────────────────── ──────────────────────── ──────────────
  y = height - 3.5%         Source line              font: 2.2% h
                     ↑ 1.5% spacing
  y = above source          Key fact (accent color)  font: 3.5% h
                     ↑ 1.5% spacing
  y = above fact             HEADLINE (white)         font: 5.5% h
                     ↑ 1.5% gap
  y = above headline         Accent bar              height: 0.5% h
```

Each text element uses:
- `_wrap_text()` — pixel-accurate word wrapping within `width - 12%` margins
- `_draw_text_with_shadow()` — 2px offset black drop shadow for readability against any background

## 2.7 Design Principles: Visual Philosophy

All image generation follows `config/visual_philosophy.md`:

```mermaid
mindmap
  root(("LESS IS MORE"))
    **One Subject,<br/>One Emotion**
      Single focal point
      No layered metaphors
      "A lone silhouette > silhouette + passports + chains + fog"
    **Negative Space<br/>Is the Design**
      50-60% of frame
      Empty sky / blur / shadow / gradient
      Gives subject its weight
    **Restrained<br/>Palette**
      2-3 dominant tones max
      One lead, one support, one accent
      Monochrome often strongest
```

### Composition Rules

| Rule | Implementation |
|------|---------------|
| **Simplicity over storytelling** | Image is one frozen moment, not a narrative illustration |
| **Shallow depth of field** | Sharp subject, soft bokeh environment — naturally reduces clutter |
| **Geometric clarity** | Clean lines, symmetry, or rule-of-thirds placement |
| **Bottom 25% reserve** | Dark zone for text overlay; doubles as visual grounding |

### What NOT To Do

| ❌ Don't | ✅ Instead |
|----------|-----------|
| Multiple symbolic objects (chains + passports + candles) | Pick the **single** strongest symbol |
| Crowded environmental detail | A **hint** of setting is enough |
| Heavy-handed metaphors | **Subtlety** is more powerful |
| Stock-photo collages | One subject with **breathing room** |

### Reference Aesthetic

> **Apple** product photography · **NYT Magazine** covers · **Amnesty International** posters · **Magnum Photos** editorial
>
> Clean, confident, one clear point of focus, quiet gravity.

---

# Part 3: Human-in-the-Loop (HITL) System

## 3.1 HITL Checkpoint Map

The pipeline has **3 intervention points** where user intent can override AI decisions. These are not simple approve/reject gates — each checkpoint offers multiple actions that reshape the downstream pipeline.

```mermaid
flowchart TD
    START(["Campaign Start"]) --> TA["Trend Analyzer"]
    TA --> CP1

    CP1["⏸ CHECKPOINT 1\nTrend Review\n──────────────\n• Approve / Re-search\n• Override topic\n• Add creative guidance"]

    CP1 --> AA["Audience Analyzer"]
    AA --> WR["Writer Agent"]
    WR --> IG["Image Generator"]
    IG --> CP2

    CP2["⏸ CHECKPOINT 2\nContent Review\n──────────────\n• Approve & Publish\n• Regen image only\n• Regen text + image\n  (with feedback)"]

    CP2 -->|approve| PUB["Publisher"]
    PUB --> CP3

    CP3["⏸ CHECKPOINT 3\nPost-Publish Refinement\n──────────────\n• Refine text only\n• Refine image only\n• Refine both\n• Change audience\n  (with feedback)"]

    CP3 -->|"creates new session\nwith pre-filled state"| AA

    style CP1 fill:#fdcb6e,color:#2d3436,stroke:#f39c12,stroke-width:3px
    style CP2 fill:#fdcb6e,color:#2d3436,stroke:#f39c12,stroke-width:3px
    style CP3 fill:#fdcb6e,color:#2d3436,stroke:#f39c12,stroke-width:3px
    style TA fill:#6ab04c,color:#fff,stroke:none
    style AA fill:#f0932b,color:#fff,stroke:none
    style WR fill:#be2edd,color:#fff,stroke:none
    style IG fill:#eb4d4b,color:#fff,stroke:none
    style PUB fill:#22a6b3,color:#fff,stroke:none
```

### Implementation: LangGraph `interrupt_after`

HITL checkpoints are powered by **LangGraph's interrupt mechanism** in `src/workflow/graph.py`:

```python
app = workflow.compile(
    checkpointer=memory,
    interrupt_after=["trend_analyzer", "image_generator"]
)
```

When `trend_analyzer` or `image_generator` finishes, LangGraph **suspends execution** and saves the full state to the `MemorySaver` checkpointer. The FastAPI endpoint returns the paused state to the frontend. When the user submits their decision, `graph.update_state()` injects the user's choices, and `graph.stream(None, config)` **resumes** from exactly where it stopped.

Checkpoint 3 (post-publish refinement) works differently — it creates an entirely **new session** with pre-filled state via the `/refine` endpoint, selectively clearing only the fields that need regeneration.

---

## 3.2 Checkpoint 1: Trend Review

**Trigger:** `status: "approving_trend"` · **Endpoint:** `POST /api/campaign/{id}/approve-trend` · **File:** `api.py:152`

```mermaid
flowchart TD
    PAUSE["Pipeline paused\nafter Trend Analyzer"] --> USER

    USER{"User action?"} -->|"Approve\n(keep AI pick)"| A1["status → 'approved_trend'\n(topic unchanged)"]
    USER -->|"Select different\narticle"| A2["Re-extract context\nvia GPT-4o-mini\ntopic → article.title"]
    USER -->|"Type custom\ntopic"| A3["Re-extract context\nvia GPT-4o-mini\ntopic → user text"]
    USER -->|"Re-search"| A4["Clear all trend data\nstatus → 'starting'\nRe-run Trend Analyzer"]

    A1 --> G["Inject user_guidance\nif provided"]
    A2 --> G
    A3 --> G
    G --> RESUME["Resume pipeline\n→ Audience Analyzer"]

    style PAUSE fill:#fdcb6e,color:#2d3436,stroke:none
    style A3 fill:#55efc4,color:#2d3436,stroke:none
    style A4 fill:#ff7675,color:#fff,stroke:none
    style G fill:#74b9ff,color:#2d3436,stroke:none
```

### User inputs at this checkpoint

| Input | State field | Priority | Downstream effect |
|-------|------------|----------|-------------------|
| **Custom topic** | `trend_topic` | **Overrides** AI-selected topic entirely | New context re-extracted via LLM; propagates to all downstream agents |
| **Article selection** | `trend_topic` | **Overrides** AI pick with chosen article | Context re-extracted from that specific article |
| **Creative guidance** | `user_guidance` | **Additive** — injected into 3 downstream agents | Audience Analyzer, Writer, and Image Generator all receive it |
| **Re-search** | Clears `trend_*` fields | **Destructive** — restarts search from scratch | Fresh `random.sample()` + Exa search cycle |

### Code: Custom topic overrides AI (api.py:181-213)

```python
if req.custom_topic and req.custom_topic.strip():
    # ★ User's custom topic REPLACES the AI-selected topic entirely
    update["trend_topic"] = req.custom_topic.strip()
    update["trend_context"] = _re_extract_context(...)   # LLM re-generates context

elif req.selected_article_title and req.selected_article_title.strip():
    # ★ User's article choice REPLACES the AI-selected topic
    update["trend_topic"] = chosen.get("title", ...)
    update["trend_context"] = _re_extract_context(...)

# else: keep AI recommendation as-is (no override)
```

**Priority rule:** `custom_topic` > `selected_article` > AI recommendation. The code checks in this exact order with early return.

---

## 3.3 Checkpoint 2: Content Review

**Trigger:** `status: "approving_image"` · **Endpoint:** `POST /api/campaign/{id}/approve-image` · **File:** `api.py:246`

```mermaid
flowchart TD
    PAUSE["Pipeline paused\nafter Image Generator"] --> USER

    USER{"User action?"} -->|"Approve\n& Publish"| A1["status → 'publisher'\n→ Publisher Agent"]
    USER -->|"Regen Image\n(+ optional feedback)"| A2["image_path → 'REJECTED'\nimage_feedback → user text\n→ Image Generator re-runs"]
    USER -->|"Regen All\n(+ optional feedback)"| A3["post_text → 'REJECTED'\nimage_path → 'REJECTED'\ntext_feedback → user text\n→ Writer + Image re-run"]

    style PAUSE fill:#fdcb6e,color:#2d3436,stroke:none
    style A1 fill:#00b894,color:#fff,stroke:none
    style A2 fill:#74b9ff,color:#2d3436,stroke:none
    style A3 fill:#a29bfe,color:#fff,stroke:none
```

### User inputs at this checkpoint

| Input | State field | Priority | Effect |
|-------|------------|----------|--------|
| **Image feedback** | `image_feedback` | **Appended** to prompt as `CRITICAL INSTRUCTION` | Directly concatenated to the end of the image prompt |
| **Text+Image feedback** | `text_feedback` + `image_feedback` | **Injected** as `REFINEMENT MODE` in Writer | Writer receives previous post + user's change request |

### Code: User feedback becomes CRITICAL INSTRUCTION (image_generator.py:147-149)

```python
feedback = state.get("image_feedback")
if feedback:
    image_prompt += f"\nCRITICAL INSTRUCTION FROM USER FOR REGENERATION: {feedback}"
```

The label `CRITICAL INSTRUCTION` is deliberate — it signals to Gemini that this directive takes precedence over the original prompt's creative direction.

### Code: Writer receives refinement as override (writer.py:47-55)

```python
text_feedback = state.get("text_feedback")
if text_feedback:
    refinement_instruction = (
        f"\n\nREFINEMENT MODE — The user reviewed the previous post and wants changes."
        f"\n\nPREVIOUS POST:\n{previous_text}"
        f"\n\nUSER FEEDBACK: {text_feedback}"
        f"\n\nRevise the post based on this feedback. Keep what works, fix what the user pointed out."
    )
```

---

## 3.4 Checkpoint 3: Post-Publish Refinement

**Trigger:** `status: "done"` · **Endpoint:** `POST /api/campaign/{id}/refine` · **File:** `api.py:288`

This checkpoint creates a **new LangGraph session** with pre-filled state, selectively clearing only the fields that need regeneration:

```mermaid
flowchart TD
    DONE["Campaign Published\n(status: done)"] --> USER

    USER{"Refine target?"} -->|"Text only"| T["Clear: post_text\nKeep: audience, image\nInject: text_feedback"]
    USER -->|"Image only"| I["Clear: image_path\nKeep: audience, text\nInject: image_feedback"]
    USER -->|"Both"| B["Clear: post_text + image\nKeep: audience\nInject: text_feedback"]
    USER -->|"Audience"| A["Clear: ALL derived fields\nKeep: trend data only\nInject: audience_feedback"]

    T --> NEW["New session created\nstatus: 'approved_trend'\nResume pipeline"]
    I --> NEW
    B --> NEW
    A --> NEW

    style DONE fill:#00b894,color:#fff,stroke:none
    style T fill:#74b9ff,color:#2d3436,stroke:none
    style I fill:#74b9ff,color:#2d3436,stroke:none
    style B fill:#a29bfe,color:#fff,stroke:none
    style A fill:#ff7675,color:#fff,stroke:none
```

### State cloning strategy (api.py:309-361)

| Target | Fields cleared | Fields kept | Feedback injected as |
|--------|---------------|-------------|---------------------|
| `text_only` | `post_text` | audience, image, visual_* | `text_feedback` → Writer |
| `image_only` | `image_path` | audience, text, visual_* | `image_feedback` → Image Generator |
| `both` | `post_text` + `image_path` | audience, visual_* | `text_feedback` → Writer |
| `audience` | ALL derived (audience, text, image, visual_*) | trend data only | `audience_feedback` → Audience Analyzer |

The Supervisor's deterministic fast-paths ensure the pipeline picks up from the right agent based on which fields are present vs. `None`.

---

## 3.5 User Input Priority: How Code Ensures User Intent Wins

The system uses **5 distinct mechanisms** to guarantee that user input always takes precedence over AI-generated content:

### Mechanism 1: Direct State Override

User input **replaces** AI-generated values at the `AgentState` level before the pipeline resumes.

```python
# api.py — custom topic overrides AI selection
update["trend_topic"] = req.custom_topic.strip()   # AI value erased
```

This is the strongest form of priority — the AI's output is simply overwritten. Used for: **custom topic**, **article selection**.

### Mechanism 2: Prompt-Level CRITICAL Labeling

User feedback is injected into LLM prompts with explicit priority labels that instruct the model to treat it as top-priority.

```python
# image_generator.py — "CRITICAL INSTRUCTION" label
image_prompt += f"\nCRITICAL INSTRUCTION FROM USER FOR REGENERATION: {feedback}"

# writer.py — "REFINEMENT MODE" section
refinement_instruction = f"\n\nREFINEMENT MODE — The user reviewed..."
    + f"\n\nUSER FEEDBACK: {text_feedback}"
    + f"\n\nRevise the post based on this feedback."

# audience_analyzer.py — "REFINEMENT" directive
f"REFINEMENT: The previous audience was '{previous_audience}'. "
f"The user wants to change the targeting. Their feedback:\n{audience_feedback}"
```

Each agent uses a different label, but the pattern is consistent: user feedback is positioned **after** the base instructions, with an explicit directive to prioritize it.

### Mechanism 3: Conditional Prompt Replacement

When a user provides a `writer_prompt`, it **replaces** the entire generated prompt body — not appended, but substituted.

```python
# writer.py:78-80
writer_prompt = state.get("writer_prompt")
if writer_prompt:
    human_content = writer_prompt + retry_instruction + refinement_instruction
    # ★ The original human_content (topic + context + audience brief) is discarded
```

### Mechanism 4: Multi-Agent Propagation

A single user input at Checkpoint 1 (`user_guidance`) propagates to **3 downstream agents**, each receiving it in their prompt:

```python
# audience_analyzer.py:110-115
if user_guidance:
    messages.append(HumanMessage(content=
        f"USER CREATIVE DIRECTION: ... Factor this into your audience selection, "
        f"visual style, and visual elements decisions:\n{user_guidance}"))

# writer.py:70-72
if user_guidance:
    human_content += f"\n\nUSER CREATIVE DIRECTION: {user_guidance}"

# image_generator.py:133-135
if user_guidance:
    user_guidance_block = f"USER CREATIVE DIRECTION (incorporate this into the scene):\n{user_guidance}"
```

### Mechanism 5: Selective State Clearing (Refinement)

The refinement endpoint uses **surgical state clearing** — only the fields that need regeneration are set to `None`, while everything else is preserved. This forces the Supervisor to route to exactly the right agent.

```python
# api.py — "text_only" refinement
prefilled.update({
    "target_audience": current_state.get("target_audience"),  # ★ KEPT
    "post_text": None,                                         # ★ CLEARED → forces Writer re-run
    "image_path": current_state.get("image_path"),            # ★ KEPT
    "text_feedback": req.feedback,                             # ★ INJECTED
})
```

---

## 3.6 Priority Propagation: One Input, Four Agents

This diagram shows how a single piece of user input (`user_guidance` from Checkpoint 1) flows through the entire pipeline:

```mermaid
flowchart TD
    USER["👤 User types guidance:\n'Focus on the survivor's strength,\nuse a hopeful tone'"] --> STATE

    STATE["AgentState.user_guidance\n= 'Focus on the survivor's...'"] --> AA & WR & IG

    AA["Audience Analyzer\n──────────────────\nReceives as:\nUSER CREATIVE DIRECTION\n→ Influences audience selection\n→ Shapes visual_style\n→ Shapes visual_elements"]

    WR["Writer Agent\n──────────────────\nReceives as:\nUSER CREATIVE DIRECTION\n→ Adapts tone to 'hopeful'\n→ Emphasizes strength angle"]

    IG["Image Generator\n──────────────────\nReceives as:\nUSER CREATIVE DIRECTION\n(incorporate into scene)\n→ Prompt reflects hope\n→ Lighter visual treatment"]

    AA -->|"visual_style: 'warm golden\ntones, soft light, hopeful'"| IG
    AA -->|"audience_brief: 'empowering\ntone, survivor focus'"| WR

    style USER fill:#fdcb6e,color:#2d3436,stroke:none
    style STATE fill:#dfe6e9,color:#2d3436,stroke:#b2bec3
    style AA fill:#f0932b,color:#fff,stroke:none
    style WR fill:#be2edd,color:#fff,stroke:none
    style IG fill:#eb4d4b,color:#fff,stroke:none
```

**Double influence on Image Generator:** Note that `user_guidance` reaches the Image Generator through **two paths**:
1. **Directly** — injected into the image prompt template as `USER CREATIVE DIRECTION`
2. **Indirectly** — it influenced the Audience Analyzer's `visual_style` and `visual_elements`, which are also fed into the image prompt

This dual-path design ensures the user's creative intent is deeply embedded in the final image, not just a superficial addition.

### Summary: User Priority Mechanisms by Checkpoint

| Checkpoint | User Input | Priority Mechanism | Code Location |
|------------|-----------|-------------------|---------------|
| **CP1** | Custom topic | **Direct Override** — replaces `trend_topic` | `api.py:182` |
| **CP1** | Article selection | **Direct Override** — replaces `trend_topic` | `api.py:196` |
| **CP1** | Creative guidance | **Multi-Agent Propagation** — 3 agents receive it | `api.py:218` |
| **CP1** | Re-search | **State Clear** — all trend data wiped, pipeline restarts | `api.py:163` |
| **CP2** | Image feedback | **CRITICAL Label** — appended to prompt with highest priority | `image_generator.py:148` |
| **CP2** | Text+Image feedback | **REFINEMENT MODE** — Writer receives previous post + feedback | `writer.py:49` |
| **CP3** | Text refinement | **Selective Clear** — only `post_text` cleared, feedback injected | `api.py:316` |
| **CP3** | Image refinement | **Selective Clear** — only `image_path` cleared, feedback injected | `api.py:328` |
| **CP3** | Audience change | **Full Clear** — all derived fields wiped, feedback to Audience Analyzer | `api.py:350` |

---

# Technology Stack Reference

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Search** | Exa (`type="neural"`) | Semantic news discovery across 13 domains |
| **Scraping Fallback** | Crawl4AI | Full article text when Exa returns metadata only |
| **Topic Analysis** | GPT-4o (`temp=0`) | Deterministic topic extraction + dedup |
| **Audience Matching** | GPT-4o-mini (`temp=0`) | Structured audience decision via Pydantic |
| **Prompt Composition** | GPT-4o-mini (`temp=0.7`) | Creative photography prompt ≤120 words |
| **Text Extraction** | GPT-4o-mini (`temp=0`) | Headline / key_fact / source for overlay |
| **Image Generation** | Gemini 3.1 Flash | Raw photograph, 4:5 aspect, 1K resolution |
| **Image Compositing** | Pillow (PIL) | Gradient mask, text overlay, accent bar |
| **Workflow Engine** | LangGraph (StateGraph) | Supervisor-worker routing + HITL interrupts |
| **Observability** | LangSmith | Tracing via `@traceable` decorators |
| **Frontend** | React 19 + Vite | Sidebar + main content layout, REST polling |
| **API** | FastAPI | REST endpoints, in-memory session store |
