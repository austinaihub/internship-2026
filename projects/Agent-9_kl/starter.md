# Getting Started — Campaign Agent

A step-by-step guide to run this project on your own computer.  
No prior programming experience required. Just follow each step in order.

---

## Part 1 — Install the Software You Need

You need two programs installed on your computer before anything else.

### 1. Python (version 3.11 or newer)

Python is the programming language the backend is written in.

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python 3.x.x"** button.
3. Run the installer.  
   ⚠️ **IMPORTANT:** On the very first screen of the installer, check the box that says **"Add Python to PATH"**. If you miss this, nothing below will work.
4. Click "Install Now" and wait for it to finish.

**How to verify it worked:**  
Open a terminal (on Windows, press `Win + R`, type `cmd`, hit Enter) and type:

```
python --version
```

You should see something like `Python 3.12.x`. If you see an error, re-install and make sure you checked "Add to PATH".

---

### 2. Node.js (version 18 or newer)

Node.js is needed to run the frontend (the part you see in your browser).

1. Go to **https://nodejs.org/**
2. Download the **LTS** version (the green button on the left).
3. Run the installer. Accept all defaults. No special checkboxes needed.

**How to verify it worked:**  
In the same terminal, type:

```
node --version
```

You should see something like `v20.x.x` or `v22.x.x`.

---

## Part 2 — Get Your API Keys

This project talks to several AI services over the internet. Each service requires a "key" — think of it as a password that lets the software use the service.

You need **three** keys. One more is optional.

### Key 1 — OpenAI API Key (Required)

This powers the text-writing brain of the system (GPT-4o).

1. Go to **https://platform.openai.com/signup** and create an account (or log in).
2. Go to **https://platform.openai.com/api-keys**
3. Click **"Create new secret key"**.
4. Copy the key immediately — you will **not** be able to see it again.
5. You will need to add a payment method and buy some credits (the minimum is $5). Without credits, API calls will fail.

### Key 2 — Google Gemini API Key (Required)

This powers the image generation (Gemini flash image model).

1. Go to **https://aistudio.google.com/apikey**
2. Sign in with your Google account.
3. Click **"Create API Key"**.
4. Copy the key.

> Gemini offers a free tier, so you may not need to pay anything for light usage.

### Key 3 — Exa API Key (Required)

This powers the news search feature that finds recent human trafficking articles.

1. Go to **https://exa.ai** and sign up for an account.
2. After signing in, go to **https://dashboard.exa.ai/api-keys**
3. Create a new key and copy it.

> Exa offers free credits when you sign up.

### Key 4 — LangSmith API Key (Optional)

LangSmith lets you see detailed logs of what each AI agent is doing. Useful for debugging, but **not required** to run the project.

1. Go to **https://smith.langchain.com/** and sign up.
2. Go to Settings → API Keys.
3. Create a key and copy it.

> If you don't want to use LangSmith, you can skip this. The project will run fine without it.

---

## Part 3 — Set Up the Project

Open a terminal and navigate to the project folder (the folder that contains this file).

### Step 1 — Install Python libraries

```
pip install -r requirements.txt
```

This installs all the Python packages the backend needs. It may take a minute or two.

> If you see a "pip not found" error, try `python -m pip install -r requirements.txt` instead.

### Step 2 — Set up your API keys

1. Find the file called **`.env.example`** in the project folder.
2. Make a copy of it, and name the copy **`.env`** (just `.env`, nothing else).  
   - On Windows: in File Explorer, copy the file, paste it, rename it to `.env`. If Windows warns you about changing the extension, click Yes.
   - Or in the terminal: `copy .env.example .env`
3. Open `.env` in any text editor (Notepad works fine).
4. Replace each placeholder with the real key you copied earlier:

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaXXXXXXXXXXXXXXXXXXXXX
EXA_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
```

5. If you skipped LangSmith, change this line:

```
LANGCHAIN_TRACING_V2=false
```

6. Save and close the file.

### Step 3 — Install frontend libraries

```
cd frontend
npm install
cd ..
```

This downloads the JavaScript packages for the browser interface. It may take a minute.

---

## Part 4 — Run the Project

You need **two terminal windows** running at the same time.

### Terminal 1 — Start the Backend

Open a terminal in the project folder and run:

```
uvicorn api:app --reload
```

You should see output like:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Leave this terminal open and running.** Do not close it.

### Terminal 2 — Start the Frontend

Open a **second** terminal in the project folder and run:

```
cd frontend
npm run dev
```

You should see output like:

```
  VITE v8.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
```

**Leave this terminal open and running too.**

### Open the App

Open your web browser (Chrome, Edge, Firefox, etc.) and go to:

```
http://localhost:5173
```

You should see the Campaign Agent interface. 🎉

---

## Part 5 — How to Use It

The system creates human trafficking awareness campaign posters in an automated pipeline. Here's what happens step by step:

### Step 1: Start a Campaign

Click the start button. Optionally type in keywords to search for (e.g., "labor trafficking Southeast Asia"). If you leave it blank, the system will search automatically.

### Step 2: Review News Articles

The system searches for recent human trafficking news. You will see a list of articles. You can:

- **Approve** the AI's recommended topic.
- **Pick a different article** from the list.
- **Type your own topic** if none of the articles interest you.
- Optionally add **creative guidance** (e.g., "focus on the victims' perspective").

### Step 3: Review Audience & Style

The system proposes a target audience and visual style. You can:

- **Approve** the suggestion as-is.
- **Edit** the target audience, visual brief, or style settings.
- **Choose a visual style preset** (e.g., Rembrandt, Cinematic Depth, etc.).

### Step 4: Review the Generated Poster

The system writes campaign text and generates an image. You will see a preview. You can:

- **Approve** it to publish.
- **Regenerate the image** (keep the text, make a new image).
- **Regenerate everything** (new text and new image).
- Add **feedback** to guide the regeneration.

### Step 5: Done

The final poster and an HTML preview are saved in the `outputs/` folder in your project directory.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python: command not found` | Re-install Python and make sure "Add to PATH" is checked. |
| `pip: command not found` | Try `python -m pip install -r requirements.txt` instead. |
| `npm: command not found` | Re-install Node.js. |
| Backend shows `OPENAI_API_KEY not set` | Make sure your `.env` file exists and the keys are filled in (no quotes around the values). |
| Frontend shows a blank page | Make sure the backend (Terminal 1) is running. Check for errors in the backend terminal. |
| Image generation fails | Check that your Gemini API key is correct. Make sure you have credits/quota remaining. |
| `ModuleNotFoundError: No module named 'xxx'` | Run `pip install -r requirements.txt` again. |
| Port 8000 already in use | Another program is using that port. Close it, or run: `uvicorn api:app --reload --port 8001` (you'll also need to update the frontend's API URL). |

---

## Stopping the Project

To stop everything, go to each terminal and press **`Ctrl + C`**. That's it.

---

## Cost Reminder

- **OpenAI** charges per API call. A single campaign run typically costs a few cents. Make sure you have credits loaded at https://platform.openai.com/settings/organization/billing.
- **Gemini** has a generous free tier. You likely won't be charged for light usage.
- **Exa** gives free search credits on sign-up. Monitor usage at https://dashboard.exa.ai.
