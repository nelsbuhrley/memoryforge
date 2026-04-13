# MemoryForge Design Specification

**Date:** 2026-04-13
**Status:** Draft
**Author:** Nels Buhrley + Claude

## Overview

MemoryForge is a full-stack AI-powered adaptive learning desktop application. Users upload study material (PDFs, text, DOCX) across any subject. The app parses material into dynamic Knowledge Units using Claude, then uses the SM-2 spaced repetition algorithm with context-aware scheduling to deliver personalized study sessions. Claude generates quizzes, grades answers, teaches new concepts, and re-teaches struggling ones. The system tracks long-term retention across years of use.

**Target user (MVP):** College student managing a full 18-credit course load, with future expansion to professionals and lifelong learners.

**Core philosophy:** Based on evidence-based learning principles from "Make It Stick" (Brown, Roediger & McDaniel):
- **Retrieval practice** — frequent low-stakes quizzing (the testing effect)
- **Spaced repetition** — review just as you begin to forget (SM-2 algorithm)
- **Interleaving** — mix problem types and subjects across sessions
- **Elaboration** — connect new knowledge to existing mental frameworks
- **Generation effect** — attempt answers before seeing them; struggle creates cognitive hooks
- **Calibration** — expose illusions of knowing; show where students think they know but don't

This is a **teaching app**, not a quiz app. Sessions are structured like a great tutor: ask before teaching, teach, practice, test, re-teach if needed.

## Architecture

### Layered Services (Approach B)

Four distinct layers sharing a single core Python library:

```
+---------------------------------------------------+
|                Electron + React                    |
|        (Dashboard, Study, Upload, etc.)            |
|                                                    |
|  preload.js -- contextBridge -- IPC security       |
+-------------------------+-------------------------+
                          | HTTP on localhost:9147 (configurable port)
+-------------------------v-------------------------+
|              FastAPI Local Server                  |
|         (thin wrapper, routes only)                |
+-------------------------+-------------------------+
                          | imports
+-------------------------v-------------------------+
|            Core Python Library                     |
|  +-----------+ +----------+ +----------------+     |
|  | SM-2      | | Claude   | | Material       |     |
|  | Engine    | | Service  | | Parser         |     |
|  | (pure     | | (agent-  | | (pymupdf +     |     |
|  |  math)    | |  sdk)    | |  text extract) |     |
|  +-----------+ +----------+ +----------------+     |
|  +-----------+ +----------+ +----------------+     |
|  | Session   | | Plan     | | Database       |     |
|  | Manager   | | Generator| | Layer (SQLite) |     |
|  +-----------+ +----------+ +----------------+     |
|  +-----------+                                     |
|  | Context-  |                                     |
|  | Aware     |                                     |
|  | Scheduler |                                     |
|  +-----------+                                     |
+---------------------------------------------------+
                          | imports
+-------------------------v-------------------------+
|          Nightly Daemon (launchd)                  |
|  - Generates/updates learning plans                |
|  - Creates new KU variations                       |
|  - Rebuilds subject corpora                        |
|  - Extracts deadlines from new material            |
|  - Pre-generates tomorrow's session content        |
+---------------------------------------------------+
```

**Key design decisions:**
- SM-2 engine is pure Python — no Claude, no network, fully deterministic and testable
- Claude Service uses a 3-layer token-efficiency pattern (inspired by claude-mem): lightweight summaries first, expand only what's needed, then generate
- Database layer owns all SQLite access — single source of truth, WAL mode for concurrent reads (daemon + API server)
- FastAPI server is intentionally thin — just routes and validation, all logic lives in core library
- Nightly daemon imports the same core library — no code duplication, just a different entry point

### Architectural Inspirations (patterns, not dependencies)

- **claude-mem's 3-layer search pattern** — search summaries, filter, then fetch full details. Applied to how MemoryForge sends context to Claude: send lightweight KU summaries first, expand relevant ones, then generate content. Keeps token costs manageable across 18 credits of material.
- **claude-mem's corpus pattern** — nightly batch builds per-subject structured summaries (topic map, weak areas, mastery levels) that daytime Claude calls reference cheaply.
- **Anki's scheduler/content separation** — SM-2 engine knows nothing about content, only timing state. Clean boundary.
- **Obsidian's local-first architecture** — all data is yours, in a readable SQLite database, no cloud lock-in. Exportable and inspectable.
- **Duolingo's session design** — mix lesson, practice, test in a single session with progress bar momentum. Streak mechanic for motivation.

## Data Model

### Knowledge Unit (KU)

The fundamental unit. Not a static flashcard — a concept that Claude generates fresh questions for each time.

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment |
| subject_id | INTEGER FK | Parent subject |
| material_id | INTEGER FK | Source document |
| concept | TEXT | Core concept statement |
| concept_summary | TEXT | Lightweight summary for 3-layer pattern |
| source_location | TEXT | Document page/section reference |
| difficulty | INTEGER | Claude's initial assessment (1-5) |
| tags | TEXT | JSON array — topic, chapter, type |
| prerequisites | TEXT | JSON array of KU IDs this depends on |
| easiness_factor | REAL | SM-2 EF, default 2.5 |
| interval | INTEGER | Days until next review |
| repetitions | INTEGER | Successful consecutive reviews |
| next_review | DATE | Next scheduled review date |
| created_at | TIMESTAMP | When KU was created |
| updated_at | TIMESTAMP | Last modification |

### Subject

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment |
| name | TEXT | e.g., "BIO 301", "Guitar" |
| description | TEXT | Optional notes |
| is_active | BOOLEAN | Whether currently studying |
| interleave_ratio | REAL | 0.0-1.0, default 0.3 (30% cross-subject) |
| grading_strictness | INTEGER | 1-3 (lenient, moderate, strict) |
| quiz_format | TEXT | "mixed", "free_response", "multiple_choice" |
| created_at | TIMESTAMP | |

### Material

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment |
| subject_id | INTEGER FK | Parent subject |
| filename | TEXT | Original filename |
| file_path | TEXT | Local storage path |
| file_type | TEXT | pdf, txt, md, docx |
| material_type | TEXT | textbook, syllabus, lecture_notes, homework |
| parse_status | TEXT | pending, processing, complete, error |
| page_count | INTEGER | For PDFs |
| structure_outline | TEXT | JSON — extracted headings/sections |
| created_at | TIMESTAMP | |

### Learning Plan

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment |
| subject_id | INTEGER FK | Parent subject |
| plan_data | TEXT | JSON — ordered topics, milestones, pacing |
| deadlines | TEXT | JSON — extracted exam/assignment dates |
| focus_areas | TEXT | JSON — Claude's recommended priorities |
| version | INTEGER | Incremented each nightly update |
| generated_at | TIMESTAMP | Last generation time |

### Session

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment |
| started_at | TIMESTAMP | |
| ended_at | TIMESTAMP | |
| total_turns | INTEGER | |
| subjects_covered | TEXT | JSON array of subject IDs |
| score_summary | TEXT | JSON — correct, incorrect, skipped counts |

### Session Turn

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment |
| session_id | INTEGER FK | Parent session |
| ku_id | INTEGER FK | Related KU (nullable for probes on new topics) |
| turn_type | TEXT | generative_probe, lesson, quiz, reteach |
| question_text | TEXT | What Claude asked/taught |
| student_response | TEXT | What the student answered |
| claude_feedback | TEXT | Claude's evaluation/discussion |
| grade | INTEGER | 0-5 SM-2 quality scale (null for lessons/probes) |
| time_taken_seconds | INTEGER | |
| created_at | TIMESTAMP | |

### Review History

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment |
| ku_id | INTEGER FK | Which KU was reviewed |
| session_turn_id | INTEGER FK | Link to the turn |
| quality | INTEGER | 0-5 SM-2 quality response |
| easiness_factor_before | REAL | EF before this review |
| easiness_factor_after | REAL | EF after this review |
| interval_before | INTEGER | Interval before |
| interval_after | INTEGER | Interval after |
| reviewed_at | TIMESTAMP | |

### Streak

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment |
| date | DATE | Study date (unique) |
| sessions_count | INTEGER | Sessions completed that day |
| total_minutes | INTEGER | Time studied |
| current_streak | INTEGER | Running streak count |
| longest_streak | INTEGER | All-time best |

### Subject Corpus (nightly-generated)

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment |
| subject_id | INTEGER FK | |
| topic_map | TEXT | JSON — structured topic hierarchy |
| weak_areas | TEXT | JSON — topics with low mastery |
| mastery_levels | TEXT | JSON — per-topic mastery percentages |
| ku_summaries | TEXT | JSON — lightweight KU list for 3-layer pattern |
| generated_at | TIMESTAMP | |

## SM-2 Algorithm Implementation

Pure Python, no Claude involvement. Exact SuperMemo SM-2 formulas:

```python
def sm2(quality: int, repetitions: int, easiness_factor: float, interval: int):
    """
    SM-2 algorithm implementation.
    
    quality: 0-5 (0=blackout, 5=perfect)
    repetitions: consecutive correct reviews
    easiness_factor: >= 1.3, default 2.5
    interval: days until next review
    """
    if quality >= 3:  # correct response
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * easiness_factor)
        repetitions += 1
    else:  # incorrect response
        repetitions = 0
        interval = 1

    # Update easiness factor
    easiness_factor = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    easiness_factor = max(1.3, easiness_factor)

    return repetitions, easiness_factor, interval
```

**Quality scale mapping:**
- 5 — perfect, immediate recall
- 4 — correct after brief hesitation
- 3 — correct with significant difficulty
- 2 — incorrect, but recognized correct answer
- 1 — incorrect, vaguely remembered
- 0 — complete blackout

Cards are never deleted. Mastered cards get longer intervals (weeks, months, years) but always come back. Failed long-term cards reset and enter re-teach flow.

## Context-Aware Scheduler

SM-2 answers "what's due?" — the scheduler answers "in what order and grouping?"

**Scheduling logic:**
1. Pull all KUs where `next_review <= today`
2. Check learning plan for new topics ready to introduce (prerequisites met)
3. Group due KUs by subject and topic proximity
4. Build session sequence:
   - Cluster 2-3 related KUs from same subject (connection-building)
   - Insert subject switches for interleaving (ratio configurable per subject)
   - Place generative probes before new topic lessons
   - Place long-term review cards in gaps between clusters
5. Respect prerequisite ordering — always review A before B if B depends on A

**Session flow pattern:**
```
Generative probe (new topic)
  -> Discussion of student's reasoning
  -> Lesson on that topic
  -> Quiz on related known concepts (cluster)
  -> Subject switch (interleave)
  -> Quiz mix from different subject
  -> Re-teach (if any failures)
  -> Long-term review card
  -> Repeat cycle...
```

## Study Session Engine

### Unified Session Feed

All interaction happens in a single scrollable feed — lessons, quizzes, probes, and re-teach flow together like a conversation with a tutor. No screen switching between modes.

**Four activity types in the feed:**

1. **Generative probe** — "What do you think happens when X?" on an unlearned topic. No grading. Captures student reasoning. Claude discusses the thought process and teaches the concept, connecting to what the student got right/wrong.

2. **Lesson** — Claude teaches a concept with elaboration prompts ("How does this connect to Y you learned last week?"). Visual indicator distinguishes from quiz turns.

3. **Quiz** — Fresh question generated from a KU. Format selected by question type registry (free response, multiple choice, fill-in-blank, apply-the-concept). More formats pluggable in the future. Graded with configurable strictness.

4. **Re-teach** — Triggered by quiz failure. Socratic questioning first (2-3 guiding questions). If student is still stuck, switches to direct explanation with elaboration. Option to immediately re-quiz.

**Side panel:** Slides out for reference material — source PDF page, KU details, related concepts, learning plan context. Never leaves the feed.

**Claude context management (3-layer pattern):**
- Claude sees: current KU, 2-3 recent turns for conversational continuity, lightweight student performance summary for this topic
- Claude does NOT see: entire history, all KUs, full documents
- Pre-generated content from nightly batch used when available to reduce latency

**Question type registry:**
- Pluggable system for quiz formats
- MVP types: free response, multiple choice, fill-in-blank, apply-the-concept
- Future types can be added (matching, diagramming, code exercises) without changing the session engine
- The engine requests "give me a question for this KU" and the registry handles format selection

### Grading

- **Free response:** Claude evaluates understanding with configurable strictness (lenient, moderate, strict) per subject
- **Multiple choice:** Automatic
- **Generative probes:** Not graded, but Claude's assessment of prior intuition stored for growth tracking ("you initially thought X, now you understand Y")

### Streak System

- Daily streak counter — study at least one session per day
- Current streak and longest streak displayed on dashboard
- Gentle reminder notification if streak at risk (evening, configurable time)

## Nightly Batch Daemon

Runs as a `launchd` service on user-configured schedule (default 2:00 AM). Imports core library directly — no API server dependency.

### Jobs (in order):

1. **Process new uploads** — parse material uploaded during the day into KUs with prerequisites and tags
2. **Update learning plans** — Claude reviews each active subject's plan against progress, deadlines, performance gaps, and new material. Adjusts topic ordering and pacing.
3. **Build subject corpora** — per-subject structured summaries (topic map, weak areas, mastery levels) for cheap daytime Claude calls
4. **Pre-generate session content** — create tomorrow's generative probes and lesson outlines for faster daytime sessions
5. **Decay detection** — scan long-term mastered KUs approaching review dates, flag for upcoming sessions
6. **Analytics rollup** — aggregate daily performance into weekly/monthly trends

### Design principles:
- Each job is idempotent — safe to re-run if interrupted
- Jobs log progress to SQLite
- Claude API unavailable: retry with backoff, pick up next night
- Token budget per night is configurable to prevent runaway costs

## Material Upload & Parsing

### Supported formats
PDF, plain text, markdown, DOCX

### Upload flow
1. User uploads file, assigns to subject
2. Optionally tags it (textbook, syllabus, lecture notes, homework)
3. Syllabus tag triggers immediate deadline/topic extraction
4. File stored locally in managed directory (path stored in DB, not the file itself)
5. Light parsing immediately (text extraction, page count, structure)
6. Deep parsing (KU extraction) queued for nightly batch OR user triggers "parse now" (available for files under 50 pages; larger files always go to nightly batch to avoid blocking daytime Claude usage)

### Parsing strategy (3-layer pattern):
1. Extract raw text and structure (chapters, headings, sections)
2. Send Claude a structural outline — Claude identifies key concepts and prerequisites
3. For each concept, send relevant text chunk — Claude generates full KU

### Security
- File uploads validated for type and size
- Files stored outside SQLite DB
- No execution of uploaded content
- File paths sanitized

## Frontend Screens

### 1. Dashboard
- Today's session summary (due cards, new topics, estimated time)
- Streak counter (current + longest)
- Quick-start study session button
- Upcoming deadlines from learning plans
- Performance snapshot (mastery % per subject)

### 2. Upload Material
- Drag-and-drop or file picker
- Assign to subject (existing or create new)
- Tag type (textbook, syllabus, lecture notes, homework)
- Parsing status indicator (queued, processing, complete)
- "Parse now" button for immediate processing

### 3. Study Session (unified feed)
- Continuous scrollable feed — lessons, quizzes, probes, re-teach all in one flow
- Subtle visual indicators per activity type (not separate modes)
- Progress bar showing session completion
- Timer per question (visible, not pressuring)
- "Go deeper" and "Skip" controls
- Slide-out side panel for reference material (source PDF, KU details, related concepts)
- Session summary at end (score, time, concepts covered, growth moments)

### 4. Learning Plan
- Per-subject roadmap view — topic tree with mastery status
- Timeline aligned to syllabus deadlines
- Claude's recommended focus areas highlighted
- Manual override to reorder or skip topics
- "Last updated" timestamp (from nightly batch)

### 5. Performance History
- Charts: mastery over time, daily time spent, streak history
- Per-subject breakdown
- Weakest topics list (sorted by fail rate)
- Long-term retention curve — old mastered topics holding up?
- Growth tracking from generative probes

### 6. Subject Library
- All subjects with material counts, KU counts, mastery %
- Expand to see uploaded materials and parse status
- Archive/reactivate subjects
- Create new subject

## Tech Stack

### Backend (Python)
- `claude-agent-sdk` — Claude API integration (replaces deprecated claude-code-sdk)
- `fastapi` + `uvicorn` — local API server
- `sqlite3` (stdlib) — database, WAL mode
- `pymupdf` (fitz) — PDF text extraction
- `python-docx` — DOCX parsing
- `pydantic` — data validation and serialization

### Frontend (Electron + React)
- `electron` (v34+) — desktop shell with context isolation
- `react` 19 — UI framework
- `react-router` — screen navigation
- `tailwindcss` — styling
- `recharts` — performance charts
- `electron-builder` — packaging

### Infrastructure
- `launchd` plist — nightly daemon scheduling (macOS)
- SQLite WAL mode — concurrent read access (daemon + API server)
- No external servers. No cloud database. Everything local.

## MVP Scope

**Included in MVP:**
- Upload material (PDF, text, DOCX) with subject assignment
- KU extraction via Claude (parse now)
- SM-2 engine with context-aware scheduling
- Unified study session feed (all 4 activity types)
- Configurable grading strictness and quiz format per subject
- Configurable interleaving (subject-focused vs. cross-subject)
- Basic learning plan generation
- Streak system
- Dashboard, study session, upload, subject library screens
- Performance history (basic charts)
- Side panel for reference material

**Deferred to v2 (with specific plans to implement):**
- Nightly batch daemon (launchd service)
- Syllabus deadline extraction
- Pre-generated session content
- Subject corpora for token efficiency
- Advanced analytics rollup
- Learning plan timeline view
- Decay detection for long-term mastered cards
- Additional question type formats
- Streak risk notifications
- Export/backup functionality

## Future Expansion Path

The layered architecture (core library + thin consumers) enables:
- **Mobile app** — new frontend consuming same API
- **Web version** — React frontend reusable
- **CLI mode** — import core library directly
- **Multi-user** — add auth layer above API server
- **Professional/lifelong learner personas** — different default settings and onboarding flows
