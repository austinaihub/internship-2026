# Campaign Agent

> AI-powered multi-agent system that generates human trafficking awareness campaigns for social media.  
> Built with LangGraph, OpenAI, Google Gemini, and React.

---

## Project Overview

| Component | Technology | How It Runs |
|---|---|---|
| Backend | Python / FastAPI + LangGraph | `uvicorn api:app` |
| Frontend | React (Vite) | Pre-built static files served by FastAPI |
| External APIs | OpenAI, Gemini, Exa API keys | Configured via `.env` |
| Database | None (in-memory sessions) | — |

---

## Deployment Strategy: One-Click "Green Deploy" Package

This project uses the **lightest possible deployment** — no Docker, no cloud services. The end user only needs to:

1. Install Python
2. Double-click `start.bat`
3. Browser opens automatically

### How It Works

| Step | Description |
|---|---|
| 1. Frontend is pre-built | `npm run build` generates `frontend/dist/`, which FastAPI serves directly |
| 2. Single process | FastAPI handles both the API and frontend — only **one** terminal needed |
| 3. `start.bat` one-click script | Automatically creates a virtual environment, installs dependencies, starts the server, and opens the browser |
| 4. Deliver as a zip | User extracts, fills in `.env`, double-clicks `start.bat` — done |

### Why Not Other Approaches?

| Approach | Problem |
|---|---|
| Docker | Small NGOs are unlikely to have Docker Desktop installed. On Windows, it also requires WSL/Hyper-V — too heavy. |
| Cloud (Vercel / Railway / Render) | Involves recurring costs, domain setup, CORS configuration, and LangGraph's long-running tasks tend to hit timeout limits. |
| **This approach: Green Deploy** | Zero extra software, zero ongoing costs, double-click to run. |

---

## Quick Start (End-User Guide)

### Prerequisites

- **Python 3.11+** — Download from [python.org](https://www.python.org/downloads/)
  - **Important:** Check **"Add Python to PATH"** during installation
- **API Keys** — You'll need the keys listed below

### Three Steps to Launch

```
Step 1:  Extract the zip file to any directory
Step 2:  Open the .env file and fill in your API keys (see below)
Step 3:  Double-click start.bat → browser opens → start using it!
```

### First-Time Setup

1. **Extract** the zip package to any location (e.g., Desktop or D: drive)
2. **Find** the `.env.example` file in the folder
3. **Copy** it and rename to `.env` (or just double-click `start.bat` — it will create one for you automatically)
4. **Open `.env` with Notepad** and fill in your API keys:

```env
# Required — OpenAI (used for text generation and analysis)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx

# Required — Google Gemini (used for image generation)
GEMINI_API_KEY=AIzaxxxxxxxxxxxxxxxx

# Required — Exa.ai (used for news search)
EXA_API_KEY=xxxxxxxxxxxxxxxx

# Optional — LangSmith (for development debugging, end users can skip)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
```

5. **Save** the `.env` file, then **double-click `start.bat`**
6. Wait for dependencies to install (first time only, approximately 2–5 minutes)
7. Browser automatically opens `http://localhost:8000` — ready to use!

### Subsequent Usage

Just **double-click `start.bat`** each time — no reinstallation needed.

---

## API Key Reference

| API | Purpose | Where to Get It | Cost |
|---|---|---|---|
| **OpenAI** | Text generation, trend analysis | [platform.openai.com](https://platform.openai.com/api-keys) | Pay-as-you-go, ~$5 minimum |
| **Google Gemini** | AI image generation | [aistudio.google.com](https://aistudio.google.com/apikey) | Free tier available |
| **Exa.ai** | News search | [dashboard.exa.ai](https://dashboard.exa.ai/api-keys) | Free tier available |
| LangSmith *(optional)* | Development tracing | [smith.langchain.com](https://smith.langchain.com/) | Free |

---

## Developer Guide

### Project Structure

```
Campaign-Agent/
├── api.py                  # FastAPI backend + static file serving
├── app.py                  # Streamlit dashboard (alternative UI)
├── main.py                 # CLI entry point
├── config.py               # Feature toggles & news source config
├── requirements.txt        # Python dependencies
├── start.bat               # One-click launcher (Windows)
├── .env.example            # Environment variable template
│
├── src/
│   ├── state.py            # AgentState definition
│   ├── agents/             # Six AI agent implementations
│   │   ├── trend_analyzer.py
│   │   ├── audience_analyzer.py
│   │   ├── writer.py
│   │   ├── image_generator.py
│   │   └── publisher.py
│   ├── tools/              # Exa search and other tools
│   └── workflow/
│       └── graph.py        # LangGraph pipeline orchestration
│
├── frontend/
│   ├── src/                # React source code
│   │   ├── App.jsx
│   │   ├── api.js          # API client
│   │   ├── pages/          # Step-by-step workflow pages
│   │   └── components/     # Shared UI components
│   ├── dist/               # Pre-built static files (production)
│   ├── package.json
│   └── vite.config.js
│
├── outputs/                # Generated images and previews
└── scripts/
    └── build_poster.py     # Poster composition script
```

### Agent Pipeline

```
Trend Analyzer (Exa news search)
       |
  [HITL Checkpoint: Select news topic]
       |
Audience Analyzer (target audience profiling)
       |
  [HITL Checkpoint: Confirm audience & visual style]
       |
Writer (GPT-4o copy generation)
       |
Image Generator (Gemini image generation)
       |
  [HITL Checkpoint: Approve final poster]
       |
Publisher (preview & export)
```

### Development Mode (Hot Reload)

If you need to modify the frontend, run in development mode:

```bash
# Terminal 1 — Backend (port 8000)
uvicorn api:app --reload

# Terminal 2 — Frontend (port 5173, with hot reload)
cd frontend
npm run dev
```

In dev mode, the frontend runs on `http://localhost:5173` and API requests are proxied to the backend via Vite.

### Rebuilding the Frontend

After modifying frontend code, rebuild the static files:

```bash
cd frontend
npm install        # Only needed the first time or when adding dependencies
npm run build      # Generates the dist/ directory
```

Restart `start.bat` to pick up the new build.

### Alternative Interfaces

```bash
# Streamlit dashboard
streamlit run app.py

# CLI with interactive HITL
python main.py
```

---

## Packaging for Delivery

How to package the project as a zip for delivery to a client:

### 1. Build the Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### 2. Exclude These Files/Directories

Do **not** include the following in the zip:

```
.env              (contains your API keys — do not share)
.venv / venv      (auto-generated on first run)
__pycache__/      (auto-generated)
node_modules/     (not needed by end users)
outputs/          (created at runtime)
.git/             (version control)
```

### 3. Include These Files/Directories

Make sure the following **are** in the zip:

```
api.py
app.py
main.py
config.py
requirements.txt
start.bat
.env.example
src/              (entire directory)
frontend/dist/    (pre-built static files)
scripts/          (entire directory)
assets/           (entire directory)
README.md
```

### 4. Create the Zip

```powershell
# PowerShell
Compress-Archive -Path api.py, app.py, main.py, config.py, requirements.txt, start.bat, ".env.example", src, "frontend/dist", scripts, assets, README.md -DestinationPath CampaignAgent.zip
```

Or manually select the files, right-click, and choose **Send to > Compressed folder**.

---

## FAQ

### Q: Double-clicking start.bat says "Python is not installed"
**A:** Download Python 3.11+ from [python.org](https://www.python.org/downloads/). During installation, **make sure** to check "Add Python to PATH". Then re-run start.bat.

### Q: The page opens but shows a blank screen
**A:** Verify that `frontend/dist/` exists and contains `index.html`. If missing, a developer needs to run `npm run build` in the frontend directory.

### Q: I'm getting API key errors
**A:** Open the `.env` file and check:
- All keys are filled in correctly (no extra spaces)
- Keys haven't expired and have sufficient balance
- OpenAI requires a funded account

### Q: Dependency installation is very slow
**A:** First-time installation takes approximately 2–5 minutes depending on your network. If you're in China, you can use a mirror:
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: How do I stop the server?
**A:** Press `Ctrl + C` in the black terminal window running start.bat, then press `Y` to confirm.

### Q: Can multiple people use it at the same time?
**A:** Technically yes, but the system is designed for single-user mode. Concurrent usage may cause session conflicts.

---

## License

MIT

---

<p align="center">
  <sub>Built with care for human trafficking awareness</sub>
</p>
