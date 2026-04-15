# MemoryForge — Setup & Run Guide

MemoryForge is an AI-powered flashcard and study app. You upload documents (PDF, Word, text), and it generates adaptive quiz questions using Claude. It tracks your progress, schedules reviews using spaced repetition (SM-2), and shows your streak and mastery over time.

---

## What You Need Before Starting

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.12 or higher | `python3 --version` |
| Node.js | 18 or higher | `node --version` |
| npm | 9 or higher | `npm --version` |
| Git | any | `git --version` |

You also need an **Anthropic API key** for the AI question-generation features.
Get one at [console.anthropic.com](https://console.anthropic.com).

---

## Step 1 — Clone the Repo

```bash
git clone git@github.com:nelsbuhrley/memoryforge.git
cd memoryforge
```

---

## Step 2 — Set Up the Backend (Python)

The backend is a FastAPI server. It handles all data storage, SM-2 scheduling, and Claude API calls.

### 2a. Create a virtual environment

```bash
cd backend
python3 -m venv .venv
```

### 2b. Activate it

```bash
source .venv/bin/activate
```

Your terminal prompt will change to show `(.venv)` — this means it's active.

### 2c. Install dependencies

```bash
pip install -e ".[dev]"
```

### 2d. Set your Anthropic API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

> **Tip:** Add this line to your `~/.zshrc` or `~/.bashrc` so you don't have to re-enter it each session.

### 2e. Verify the backend works

```bash
python -m uvicorn memoryforge.api.app:create_app --factory --host 127.0.0.1 --port 9147
```

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:9147
```

Stop it with `Ctrl+C`. Setup is good.

---

## Step 3 — Set Up the Frontend (Node.js)

The frontend is an Electron + React app.

```bash
cd ../frontend
npm install
```

---

## Running the App

There are two ways to run MemoryForge: **Dev Mode** and **Production Mode**.

---

### Option A: Dev Mode (Recommended for Now)

Dev mode gives you live reload and browser DevTools. You need **two terminals**.

**Terminal 1 — Start the backend:**

```bash
cd memoryforge/backend
source .venv/bin/activate
export ANTHROPIC_API_KEY="sk-ant-..."
python -m uvicorn memoryforge.api.app:create_app --factory --host 127.0.0.1 --port 9147
```

Wait until you see `Application startup complete.`

**Terminal 2 — Start the frontend:**

```bash
cd memoryforge/frontend
npm run dev
```

An Electron window will open automatically. The app is running.

> The Electron window connects to the backend at `http://127.0.0.1:9147`.

---

### Option B: Production Mode

In production mode, the Electron app starts and stops the backend automatically — no second terminal needed.

**Step 1:** Build the frontend:
```bash
cd frontend
npm run build
```

**Step 2:** Launch:
```bash
npx electron .
```

The app opens, starts the backend silently, and shuts it down when you close the window.

---

## Where Your Data Lives

All data is stored in your home directory:

```
~/.memoryforge/
├── memoryforge.db    ← SQLite database (subjects, sessions, progress)
└── uploads/          ← Uploaded documents
```

No cloud sync. Everything stays on your machine.

---

## Using the App

Once running, here is the typical workflow:

### 1. Create a Subject
Go to **Subjects** in the sidebar → click **New Subject** → enter a name (e.g. "Physics") → click **Create**.

### 2. Upload Material
Go to **Upload** → select your subject → click **Choose File** → pick a `.pdf`, `.docx`, `.txt`, or `.md` file → click **Upload**.

After uploading, click **Parse Now** on the material card. This triggers Claude to extract knowledge units from the document. It may take 10–60 seconds depending on document length.

### 3. Study
Go to **Study** in the sidebar → select a subject (or leave "All subjects") → click **Start Session**.

- A question appears based on your material.
- Type your answer in the text box.
- Click **Submit** (or press `Cmd+Enter`).
- Claude grades your answer and gives feedback.
- Keep going until you click **End Session**.

Your results (correct/incorrect, grade 1–5) are saved and feed the SM-2 spaced repetition scheduler.

### 4. Check Your Dashboard
The **Dashboard** shows:
- **Due Today** — how many knowledge units are scheduled for review
- **Current Streak** — consecutive days you've studied
- **Subject Mastery** — % of each subject's knowledge units you've mastered

### 5. Review History
**History** shows all past reviews with a grade, correct/incorrect badge, and an accuracy-over-time chart.

---

## Running Tests

**Backend tests (108 tests):**
```bash
cd backend
source .venv/bin/activate
python -m pytest
```

**Frontend tests (25 tests):**
```bash
cd frontend
npm test
```

---

## Troubleshooting

**Electron window is blank / "cannot connect"**
- Make sure the backend is running first (Terminal 1 step above).
- Confirm it shows `Application startup complete` before opening the frontend.

**"ANTHROPIC_API_KEY not set" error**
- Run `export ANTHROPIC_API_KEY="sk-ant-..."` in the terminal where you start the backend.

**Parse hangs or never completes**
- Check that your API key is valid and has credits at [console.anthropic.com](https://console.anthropic.com).
- Large PDFs can take up to 60 seconds.

**Port 9147 already in use**
```bash
lsof -i :9147
kill -9 <PID>
```
Then restart the backend.

**npm install fails**
- Make sure you're on Node 18+: `node --version`
- Try deleting `node_modules` and running `npm install` again.

**Backend venv not found (production mode)**
- Production mode expects the venv at `backend/.venv`.
- Re-run Step 2 from the root of the cloned repo.
