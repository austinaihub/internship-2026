# Update Log

## [2026-03-16] Instagram 4:5 Aspect Ratio & SDK Migration

### Changes
- **`requirements.txt`** — Replaced `google-generativeai` with `google-genai` (new official SDK).
- **`src/agents/image_generator.py`** — Migrated from `genai.GenerativeModel` (legacy) to `genai.Client` with `client.models.generate_content`. Added `types.ImageConfig(aspect_ratio="4:5", image_size="1K")` to natively output Instagram portrait-format (4:5) images at 1024px resolution.

### Why
The legacy `google-generativeai` SDK does not expose `image_config`, making aspect ratio control impossible. The new `google-genai` SDK supports `ImageConfig` with native `aspect_ratio` and `image_size` parameters for `gemini-3.1-flash-image-preview`.

### Supported aspect ratios on `gemini-3.1-flash-image-preview`
`1:1` `3:2` `2:3` `4:3` `3:4` `**4:5**` `5:4` `9:16` `16:9` `21:9` `1:4` `4:1` `1:8` `8:1`

---

## [2026-03-16] Supervisor Agent Architecture

### Changes
- **`src/agents/supervisor.py`** [NEW] — LLM-powered Supervisor (`gpt-4o-mini`) with structured output (`RouteDecision`) to dynamically route between workers. Includes retry tracking and reasoning logging.
- **`src/agents/planner.py`** [DELETED] — Fully replaced by the Supervisor.
- **`src/workflow/graph.py`** — Rewritten: `START → Supervisor → [workers] → Supervisor → … → END`. Publisher routes directly to END.
- **`src/state.py`** — Added `next`, `run_id`, `retry_counts`, `messages` fields.
- **`main.py`** — `thread_id` now uses `uuid.uuid4()` per run; bootstraps `retry_counts` and `messages`.

### Why
The rule-based Planner could not handle edge cases (off-topic trends, cascading errors, repeated rejections). The Supervisor uses LLM reasoning for dynamic routing and graceful error recovery.
