# Campaign Agent

Multi-agent AI system that generates human trafficking awareness campaigns for social media. Built with LangGraph, OpenAI, and Google Gemini.

## How It Works

Six specialized agents run in a supervised pipeline:

**Trend Analyzer** (Exa search) → **Audience Analyzer** → **Writer** (GPT-4o) → **Image Generator** (Gemini) → **Publisher**

Human-in-the-loop checkpoints pause after trend analysis and image generation for review and approval.

## Prerequisites

- Python 3.11+
- Node.js 18+
- API keys: OpenAI, Google Gemini, Exa.ai, LangSmith (optional)

## Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and fill in your API keys

# 3. Install frontend dependencies
cd frontend
npm install
cd ..
```

## Run

Start the backend and frontend in two terminals:

```bash
# Terminal 1 — Backend (port 8000)
uvicorn api:app --reload

# Terminal 2 — Frontend (port 5173)
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

## Alternative Interfaces

```bash
# Streamlit dashboard
streamlit run app.py

# CLI with interactive HITL
python main.py
```

## Project Structure

```
api.py              FastAPI backend
app.py              Streamlit dashboard
main.py             CLI entry point
config.py           Feature toggles
src/
  state.py          AgentState definition
  agents/           Six agent implementations
  workflow/graph.py LangGraph pipeline
frontend/           React UI (Vite)
outputs/            Generated images and previews
```
