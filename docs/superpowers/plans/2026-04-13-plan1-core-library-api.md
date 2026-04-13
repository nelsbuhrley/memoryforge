# MemoryForge Plan 1: Core Library + API Server

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete Python backend — database layer, SM-2 engine, Claude service, material parser, context-aware scheduler, session engine, and FastAPI API server — fully testable via pytest and API calls.

**Architecture:** Layered Python package (`memoryforge/`) with a clean core library consumed by a thin FastAPI server. Each module has a single responsibility and communicates through well-defined interfaces. SQLite with WAL mode for concurrent access. Claude integration via `claude-agent-sdk` with a 3-layer token-efficiency pattern.

**Tech Stack:** Python 3.12+, FastAPI, uvicorn, sqlite3 (stdlib), claude-agent-sdk, pymupdf (fitz), python-docx, pydantic, pytest

---

## File Structure

```
memoryforge/
├── docs/                          # (already exists)
├── backend/
│   ├── pyproject.toml             # Package config, dependencies
│   ├── memoryforge/
│   │   ├── __init__.py
│   │   ├── config.py              # App configuration (paths, ports, defaults)
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py      # SQLite connection manager (WAL mode)
│   │   │   ├── schema.sql         # All CREATE TABLE statements
│   │   │   └── repository.py      # CRUD operations for all tables
│   │   ├── sm2/
│   │   │   ├── __init__.py
│   │   │   └── engine.py          # Pure SM-2 algorithm (no dependencies)
│   │   ├── scheduler/
│   │   │   ├── __init__.py
│   │   │   └── context_aware.py   # Context-aware session builder
│   │   ├── claude_service/
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # Claude agent-sdk wrapper
│   │   │   ├── prompts.py         # All prompt templates
│   │   │   └── three_layer.py     # 3-layer token-efficiency pattern
│   │   ├── parser/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_parser.py      # PDF text extraction (pymupdf)
│   │   │   ├── docx_parser.py     # DOCX text extraction
│   │   │   ├── text_parser.py     # Plain text / markdown
│   │   │   └── material_processor.py  # Orchestrates parsing + KU extraction
│   │   ├── session/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py          # Study session orchestrator
│   │   │   ├── question_registry.py   # Pluggable question type system
│   │   │   └── grader.py          # Grading logic (Claude + auto)
│   │   ├── streak/
│   │   │   ├── __init__.py
│   │   │   └── tracker.py         # Streak calculation and updates
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── app.py             # FastAPI app factory
│   │       ├── routes_subjects.py # Subject CRUD endpoints
│   │       ├── routes_materials.py    # Upload + parsing endpoints
│   │       ├── routes_sessions.py     # Study session endpoints
│   │       ├── routes_dashboard.py    # Dashboard data endpoints
│   │       ├── routes_plans.py        # Learning plan endpoints
│   │       └── routes_history.py      # Performance history endpoints
│   └── tests/
│       ├── conftest.py            # Shared fixtures (test DB, etc.)
│       ├── test_sm2.py            # SM-2 algorithm tests
│       ├── test_db.py             # Database layer tests
│       ├── test_scheduler.py      # Context-aware scheduler tests
│       ├── test_parser.py         # Material parsing tests
│       ├── test_session.py        # Session engine tests
│       ├── test_streak.py         # Streak tracker tests
│       ├── test_question_registry.py  # Question type registry tests
│       ├── test_grader.py         # Grading tests
│       └── test_api.py            # API endpoint integration tests
```

---

## Task 1: Project Scaffolding + .gitignore

**Files:**
- Create: `.gitignore`
- Create: `backend/pyproject.toml`
- Create: `backend/memoryforge/__init__.py`
- Create: `backend/memoryforge/config.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Create .gitignore at repo root**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg-info/
*.egg
dist/
build/
.eggs/
*.whl

# Virtual environments
.venv/
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment / secrets
.env
.env.local
*.pem
*.key

# SQLite databases
*.db
*.sqlite
*.sqlite3

# Uploaded materials (managed by app, not committed)
uploads/

# Electron
node_modules/
out/
dist-electron/

# Test / coverage
.coverage
htmlcov/
.pytest_cache/

# Logs
*.log
logs/

# Nightly daemon
*.plist.bak
```

- [ ] **Step 2: Create backend/pyproject.toml**

```toml
[project]
name = "memoryforge"
version = "0.1.0"
description = "AI-powered adaptive learning system"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.34.0",
    "pydantic>=2.10.0",
    "claude-agent-sdk>=0.1.0",
    "pymupdf>=1.25.0",
    "python-docx>=1.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.28.0",
]

[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 3: Create backend/memoryforge/__init__.py**

```python
"""MemoryForge - AI-powered adaptive learning system."""

__version__ = "0.1.0"
```

- [ ] **Step 4: Create backend/memoryforge/config.py**

```python
"""Application configuration."""

from pathlib import Path
from pydantic import BaseModel


class Config(BaseModel):
    """MemoryForge configuration."""

    db_path: Path = Path.home() / ".memoryforge" / "memoryforge.db"
    uploads_dir: Path = Path.home() / ".memoryforge" / "uploads"
    api_host: str = "127.0.0.1"
    api_port: int = 9147
    max_upload_size_mb: int = 100
    parse_now_max_pages: int = 50
    default_easiness_factor: float = 2.5
    default_interleave_ratio: float = 0.3
    nightly_token_budget: int = 100000

    def ensure_dirs(self) -> None:
        """Create required directories if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)


def get_config() -> Config:
    """Return the application config."""
    return Config()
```

- [ ] **Step 5: Create backend/tests/conftest.py**

```python
"""Shared test fixtures."""

import sqlite3
from pathlib import Path

import pytest

from memoryforge.config import Config
from memoryforge.db.connection import get_connection
from memoryforge.db.repository import Repository


@pytest.fixture
def test_config(tmp_path: Path) -> Config:
    """Config pointing to a temporary directory."""
    return Config(
        db_path=tmp_path / "test.db",
        uploads_dir=tmp_path / "uploads",
    )


@pytest.fixture
def test_db(test_config: Config) -> sqlite3.Connection:
    """Initialized test database connection."""
    test_config.ensure_dirs()
    conn = get_connection(test_config.db_path)
    return conn


@pytest.fixture
def repo(test_db: sqlite3.Connection) -> Repository:
    """Repository backed by the test database."""
    return Repository(test_db)
```

- [ ] **Step 6: Verify project structure**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -c "from memoryforge.config import get_config; c = get_config(); print(c.api_port)"`
Expected: `9147`

- [ ] **Step 7: Commit**

```bash
git add .gitignore backend/pyproject.toml backend/memoryforge/__init__.py backend/memoryforge/config.py backend/tests/conftest.py
git commit -m "feat: project scaffolding with config and test fixtures"
```

---

## Task 2: Database Layer

**Files:**
- Create: `backend/memoryforge/db/__init__.py`
- Create: `backend/memoryforge/db/schema.sql`
- Create: `backend/memoryforge/db/connection.py`
- Create: `backend/memoryforge/db/repository.py`
- Create: `backend/tests/test_db.py`

- [ ] **Step 1: Write failing database tests**

```python
"""Tests for the database layer."""

import sqlite3
from datetime import date, datetime

from memoryforge.db.repository import Repository


class TestSubjectCRUD:
    def test_create_subject(self, repo: Repository):
        subject_id = repo.create_subject(
            name="BIO 301",
            description="Molecular Biology",
        )
        assert subject_id == 1

    def test_get_subject(self, repo: Repository):
        repo.create_subject(name="BIO 301", description="Molecular Biology")
        subject = repo.get_subject(1)
        assert subject["name"] == "BIO 301"
        assert subject["is_active"] == 1
        assert subject["interleave_ratio"] == 0.3
        assert subject["grading_strictness"] == 2
        assert subject["quiz_format"] == "mixed"

    def test_list_subjects(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        repo.create_subject(name="HIST 200")
        subjects = repo.list_subjects()
        assert len(subjects) == 2

    def test_update_subject(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        repo.update_subject(1, name="BIO 302", grading_strictness=3)
        subject = repo.get_subject(1)
        assert subject["name"] == "BIO 302"
        assert subject["grading_strictness"] == 3

    def test_archive_subject(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        repo.update_subject(1, is_active=False)
        subject = repo.get_subject(1)
        assert subject["is_active"] == 0


class TestMaterialCRUD:
    def test_create_material(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        mat_id = repo.create_material(
            subject_id=1,
            filename="textbook.pdf",
            file_path="/uploads/textbook.pdf",
            file_type="pdf",
            material_type="textbook",
            page_count=350,
        )
        assert mat_id == 1

    def test_get_material(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        repo.create_material(
            subject_id=1,
            filename="textbook.pdf",
            file_path="/uploads/textbook.pdf",
            file_type="pdf",
            material_type="textbook",
            page_count=350,
        )
        mat = repo.get_material(1)
        assert mat["filename"] == "textbook.pdf"
        assert mat["parse_status"] == "pending"

    def test_list_materials_by_subject(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        repo.create_material(
            subject_id=1, filename="ch1.pdf", file_path="/a",
            file_type="pdf", material_type="textbook",
        )
        repo.create_material(
            subject_id=1, filename="ch2.pdf", file_path="/b",
            file_type="pdf", material_type="textbook",
        )
        mats = repo.list_materials(subject_id=1)
        assert len(mats) == 2


class TestKnowledgeUnitCRUD:
    def test_create_ku(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        repo.create_material(
            subject_id=1, filename="ch1.pdf", file_path="/a",
            file_type="pdf", material_type="textbook",
        )
        ku_id = repo.create_ku(
            subject_id=1,
            material_id=1,
            concept="Mitochondria produce ATP via oxidative phosphorylation",
            concept_summary="Mitochondria: ATP production",
            source_location="Chapter 5, page 102",
            difficulty=3,
            tags='["biology", "cell-biology", "chapter-5"]',
            prerequisites="[]",
        )
        assert ku_id == 1

    def test_get_ku(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        repo.create_material(
            subject_id=1, filename="ch1.pdf", file_path="/a",
            file_type="pdf", material_type="textbook",
        )
        repo.create_ku(
            subject_id=1, material_id=1,
            concept="Mitochondria produce ATP",
            concept_summary="Mitochondria: ATP",
            source_location="p102", difficulty=3,
            tags="[]", prerequisites="[]",
        )
        ku = repo.get_ku(1)
        assert ku["concept"] == "Mitochondria produce ATP"
        assert ku["easiness_factor"] == 2.5
        assert ku["interval"] == 0
        assert ku["repetitions"] == 0

    def test_get_due_kus(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        repo.create_material(
            subject_id=1, filename="ch1.pdf", file_path="/a",
            file_type="pdf", material_type="textbook",
        )
        repo.create_ku(
            subject_id=1, material_id=1,
            concept="Concept A", concept_summary="A",
            source_location="p1", difficulty=2,
            tags="[]", prerequisites="[]",
        )
        # New KU with next_review=NULL should be due
        due = repo.get_due_kus(today=date.today())
        assert len(due) == 1

    def test_update_ku_sm2_state(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        repo.create_material(
            subject_id=1, filename="ch1.pdf", file_path="/a",
            file_type="pdf", material_type="textbook",
        )
        repo.create_ku(
            subject_id=1, material_id=1,
            concept="Concept A", concept_summary="A",
            source_location="p1", difficulty=2,
            tags="[]", prerequisites="[]",
        )
        repo.update_ku_sm2(
            ku_id=1,
            easiness_factor=2.6,
            interval=1,
            repetitions=1,
            next_review=date(2026, 4, 14),
        )
        ku = repo.get_ku(1)
        assert ku["easiness_factor"] == 2.6
        assert ku["interval"] == 1
        assert ku["repetitions"] == 1


class TestSessionCRUD:
    def test_create_session(self, repo: Repository):
        session_id = repo.create_session()
        assert session_id == 1

    def test_create_session_turn(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        repo.create_material(
            subject_id=1, filename="ch1.pdf", file_path="/a",
            file_type="pdf", material_type="textbook",
        )
        repo.create_ku(
            subject_id=1, material_id=1,
            concept="A", concept_summary="A",
            source_location="p1", difficulty=2,
            tags="[]", prerequisites="[]",
        )
        session_id = repo.create_session()
        turn_id = repo.create_session_turn(
            session_id=session_id,
            ku_id=1,
            turn_type="quiz",
            question_text="What do mitochondria produce?",
            student_response="ATP",
            claude_feedback="Correct!",
            grade=5,
            time_taken_seconds=12,
        )
        assert turn_id == 1

    def test_end_session(self, repo: Repository):
        session_id = repo.create_session()
        repo.end_session(
            session_id=session_id,
            subjects_covered="[1]",
            score_summary='{"correct": 5, "incorrect": 1, "skipped": 0}',
        )
        session = repo.get_session(session_id)
        assert session["ended_at"] is not None
        assert session["subjects_covered"] == "[1]"


class TestReviewHistory:
    def test_create_review(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        repo.create_material(
            subject_id=1, filename="ch1.pdf", file_path="/a",
            file_type="pdf", material_type="textbook",
        )
        repo.create_ku(
            subject_id=1, material_id=1,
            concept="A", concept_summary="A",
            source_location="p1", difficulty=2,
            tags="[]", prerequisites="[]",
        )
        session_id = repo.create_session()
        turn_id = repo.create_session_turn(
            session_id=session_id, ku_id=1, turn_type="quiz",
            question_text="Q?", student_response="A",
            claude_feedback="OK", grade=4, time_taken_seconds=10,
        )
        review_id = repo.create_review(
            ku_id=1,
            session_turn_id=turn_id,
            quality=4,
            ef_before=2.5,
            ef_after=2.5,
            interval_before=0,
            interval_after=1,
        )
        assert review_id == 1

    def test_get_review_history_for_ku(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        repo.create_material(
            subject_id=1, filename="ch1.pdf", file_path="/a",
            file_type="pdf", material_type="textbook",
        )
        repo.create_ku(
            subject_id=1, material_id=1,
            concept="A", concept_summary="A",
            source_location="p1", difficulty=2,
            tags="[]", prerequisites="[]",
        )
        session_id = repo.create_session()
        turn_id = repo.create_session_turn(
            session_id=session_id, ku_id=1, turn_type="quiz",
            question_text="Q?", student_response="A",
            claude_feedback="OK", grade=4, time_taken_seconds=10,
        )
        repo.create_review(
            ku_id=1, session_turn_id=turn_id, quality=4,
            ef_before=2.5, ef_after=2.5,
            interval_before=0, interval_after=1,
        )
        history = repo.get_review_history(ku_id=1)
        assert len(history) == 1
        assert history[0]["quality"] == 4


class TestStreakCRUD:
    def test_record_study_day(self, repo: Repository):
        repo.record_study_day(
            study_date=date(2026, 4, 13),
            sessions_count=2,
            total_minutes=45,
        )
        streak = repo.get_streak_info()
        assert streak["current_streak"] == 1
        assert streak["longest_streak"] == 1

    def test_consecutive_days_increment_streak(self, repo: Repository):
        repo.record_study_day(date(2026, 4, 12), 1, 30)
        repo.record_study_day(date(2026, 4, 13), 1, 30)
        streak = repo.get_streak_info()
        assert streak["current_streak"] == 2
        assert streak["longest_streak"] == 2

    def test_gap_resets_streak(self, repo: Repository):
        repo.record_study_day(date(2026, 4, 10), 1, 30)
        # Skip April 11
        repo.record_study_day(date(2026, 4, 12), 1, 30)
        streak = repo.get_streak_info()
        assert streak["current_streak"] == 1
        assert streak["longest_streak"] == 1


class TestLearningPlan:
    def test_create_plan(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        plan_id = repo.create_learning_plan(
            subject_id=1,
            plan_data='{"topics": ["cell biology", "genetics"]}',
            deadlines='{"midterm": "2026-05-01"}',
            focus_areas='["cell biology"]',
        )
        assert plan_id == 1

    def test_get_plan(self, repo: Repository):
        repo.create_subject(name="BIO 301")
        repo.create_learning_plan(
            subject_id=1,
            plan_data='{"topics": ["cell biology"]}',
            deadlines="{}",
            focus_areas="[]",
        )
        plan = repo.get_learning_plan(subject_id=1)
        assert plan["version"] == 1
        assert '"cell biology"' in plan["plan_data"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'memoryforge.db'`

- [ ] **Step 3: Create db/__init__.py**

```python
"""Database layer for MemoryForge."""
```

- [ ] **Step 4: Create schema.sql**

```sql
-- MemoryForge database schema

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    is_active BOOLEAN DEFAULT 1,
    interleave_ratio REAL DEFAULT 0.3,
    grading_strictness INTEGER DEFAULT 2,
    quiz_format TEXT DEFAULT 'mixed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    material_type TEXT DEFAULT 'textbook',
    parse_status TEXT DEFAULT 'pending',
    page_count INTEGER,
    structure_outline TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    material_id INTEGER NOT NULL REFERENCES materials(id),
    concept TEXT NOT NULL,
    concept_summary TEXT NOT NULL,
    source_location TEXT,
    difficulty INTEGER DEFAULT 3,
    tags TEXT DEFAULT '[]',
    prerequisites TEXT DEFAULT '[]',
    easiness_factor REAL DEFAULT 2.5,
    interval INTEGER DEFAULT 0,
    repetitions INTEGER DEFAULT 0,
    next_review DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    plan_data TEXT NOT NULL DEFAULT '{}',
    deadlines TEXT NOT NULL DEFAULT '{}',
    focus_areas TEXT NOT NULL DEFAULT '[]',
    version INTEGER DEFAULT 1,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    total_turns INTEGER DEFAULT 0,
    subjects_covered TEXT DEFAULT '[]',
    score_summary TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS session_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    ku_id INTEGER REFERENCES knowledge_units(id),
    turn_type TEXT NOT NULL,
    question_text TEXT,
    student_response TEXT,
    claude_feedback TEXT,
    grade INTEGER,
    time_taken_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS review_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ku_id INTEGER NOT NULL REFERENCES knowledge_units(id),
    session_turn_id INTEGER NOT NULL REFERENCES session_turns(id),
    quality INTEGER NOT NULL,
    easiness_factor_before REAL NOT NULL,
    easiness_factor_after REAL NOT NULL,
    interval_before INTEGER NOT NULL,
    interval_after INTEGER NOT NULL,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS streaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    sessions_count INTEGER DEFAULT 0,
    total_minutes INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS subject_corpora (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    topic_map TEXT DEFAULT '{}',
    weak_areas TEXT DEFAULT '[]',
    mastery_levels TEXT DEFAULT '{}',
    ku_summaries TEXT DEFAULT '[]',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ku_next_review ON knowledge_units(next_review);
CREATE INDEX IF NOT EXISTS idx_ku_subject ON knowledge_units(subject_id);
CREATE INDEX IF NOT EXISTS idx_materials_subject ON materials(subject_id);
CREATE INDEX IF NOT EXISTS idx_turns_session ON session_turns(session_id);
CREATE INDEX IF NOT EXISTS idx_review_ku ON review_history(ku_id);
CREATE INDEX IF NOT EXISTS idx_streaks_date ON streaks(date);
```

- [ ] **Step 5: Create connection.py**

```python
"""SQLite connection manager."""

import sqlite3
from pathlib import Path


_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Create and initialize a SQLite connection with WAL mode."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    schema = _SCHEMA_PATH.read_text()
    conn.executescript(schema)
    conn.commit()

    return conn
```

- [ ] **Step 6: Create repository.py**

```python
"""CRUD operations for all MemoryForge tables."""

import sqlite3
from datetime import date, timedelta
from typing import Any


class Repository:
    """Single entry point for all database operations."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    # --- Subjects ---

    def create_subject(
        self,
        name: str,
        description: str = "",
        interleave_ratio: float = 0.3,
        grading_strictness: int = 2,
        quiz_format: str = "mixed",
    ) -> int:
        cursor = self.conn.execute(
            """INSERT INTO subjects (name, description, interleave_ratio,
               grading_strictness, quiz_format)
               VALUES (?, ?, ?, ?, ?)""",
            (name, description, interleave_ratio, grading_strictness, quiz_format),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_subject(self, subject_id: int) -> dict[str, Any]:
        row = self.conn.execute(
            "SELECT * FROM subjects WHERE id = ?", (subject_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_subjects(self, active_only: bool = False) -> list[dict[str, Any]]:
        if active_only:
            rows = self.conn.execute(
                "SELECT * FROM subjects WHERE is_active = 1"
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM subjects").fetchall()
        return [dict(r) for r in rows]

    def update_subject(self, subject_id: int, **kwargs: Any) -> None:
        if not kwargs:
            return
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [subject_id]
        self.conn.execute(
            f"UPDATE subjects SET {sets} WHERE id = ?", values
        )
        self.conn.commit()

    # --- Materials ---

    def create_material(
        self,
        subject_id: int,
        filename: str,
        file_path: str,
        file_type: str,
        material_type: str = "textbook",
        page_count: int | None = None,
    ) -> int:
        cursor = self.conn.execute(
            """INSERT INTO materials (subject_id, filename, file_path,
               file_type, material_type, page_count)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (subject_id, filename, file_path, file_type, material_type, page_count),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_material(self, material_id: int) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM materials WHERE id = ?", (material_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_materials(self, subject_id: int | None = None) -> list[dict[str, Any]]:
        if subject_id:
            rows = self.conn.execute(
                "SELECT * FROM materials WHERE subject_id = ?", (subject_id,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM materials").fetchall()
        return [dict(r) for r in rows]

    def update_material_status(self, material_id: int, status: str, structure_outline: str | None = None) -> None:
        if structure_outline:
            self.conn.execute(
                "UPDATE materials SET parse_status = ?, structure_outline = ? WHERE id = ?",
                (status, structure_outline, material_id),
            )
        else:
            self.conn.execute(
                "UPDATE materials SET parse_status = ? WHERE id = ?",
                (status, material_id),
            )
        self.conn.commit()

    # --- Knowledge Units ---

    def create_ku(
        self,
        subject_id: int,
        material_id: int,
        concept: str,
        concept_summary: str,
        source_location: str,
        difficulty: int,
        tags: str,
        prerequisites: str,
    ) -> int:
        cursor = self.conn.execute(
            """INSERT INTO knowledge_units (subject_id, material_id, concept,
               concept_summary, source_location, difficulty, tags, prerequisites)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (subject_id, material_id, concept, concept_summary,
             source_location, difficulty, tags, prerequisites),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_ku(self, ku_id: int) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM knowledge_units WHERE id = ?", (ku_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_due_kus(self, today: date, subject_id: int | None = None) -> list[dict[str, Any]]:
        if subject_id:
            rows = self.conn.execute(
                """SELECT * FROM knowledge_units
                   WHERE (next_review IS NULL OR next_review <= ?)
                   AND subject_id = ?
                   ORDER BY next_review ASC NULLS FIRST""",
                (today.isoformat(), subject_id),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """SELECT * FROM knowledge_units
                   WHERE next_review IS NULL OR next_review <= ?
                   ORDER BY next_review ASC NULLS FIRST""",
                (today.isoformat(),),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_kus_by_subject(self, subject_id: int) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM knowledge_units WHERE subject_id = ?", (subject_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def update_ku_sm2(
        self,
        ku_id: int,
        easiness_factor: float,
        interval: int,
        repetitions: int,
        next_review: date,
    ) -> None:
        self.conn.execute(
            """UPDATE knowledge_units
               SET easiness_factor = ?, interval = ?, repetitions = ?,
                   next_review = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (easiness_factor, interval, repetitions, next_review.isoformat(), ku_id),
        )
        self.conn.commit()

    # --- Learning Plans ---

    def create_learning_plan(
        self,
        subject_id: int,
        plan_data: str,
        deadlines: str,
        focus_areas: str,
    ) -> int:
        cursor = self.conn.execute(
            """INSERT INTO learning_plans (subject_id, plan_data, deadlines, focus_areas)
               VALUES (?, ?, ?, ?)""",
            (subject_id, plan_data, deadlines, focus_areas),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_learning_plan(self, subject_id: int) -> dict[str, Any] | None:
        row = self.conn.execute(
            """SELECT * FROM learning_plans
               WHERE subject_id = ?
               ORDER BY version DESC LIMIT 1""",
            (subject_id,),
        ).fetchone()
        return dict(row) if row else None

    # --- Sessions ---

    def create_session(self) -> int:
        cursor = self.conn.execute("INSERT INTO sessions DEFAULT VALUES")
        self.conn.commit()
        return cursor.lastrowid

    def get_session(self, session_id: int) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return dict(row) if row else None

    def end_session(
        self,
        session_id: int,
        subjects_covered: str,
        score_summary: str,
    ) -> None:
        total = self.conn.execute(
            "SELECT COUNT(*) FROM session_turns WHERE session_id = ?",
            (session_id,),
        ).fetchone()[0]
        self.conn.execute(
            """UPDATE sessions
               SET ended_at = CURRENT_TIMESTAMP, total_turns = ?,
                   subjects_covered = ?, score_summary = ?
               WHERE id = ?""",
            (total, subjects_covered, score_summary, session_id),
        )
        self.conn.commit()

    def create_session_turn(
        self,
        session_id: int,
        ku_id: int | None,
        turn_type: str,
        question_text: str,
        student_response: str | None,
        claude_feedback: str | None,
        grade: int | None,
        time_taken_seconds: int | None,
    ) -> int:
        cursor = self.conn.execute(
            """INSERT INTO session_turns (session_id, ku_id, turn_type,
               question_text, student_response, claude_feedback, grade,
               time_taken_seconds)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, ku_id, turn_type, question_text,
             student_response, claude_feedback, grade, time_taken_seconds),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_session_turns(self, session_id: int) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM session_turns WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Review History ---

    def create_review(
        self,
        ku_id: int,
        session_turn_id: int,
        quality: int,
        ef_before: float,
        ef_after: float,
        interval_before: int,
        interval_after: int,
    ) -> int:
        cursor = self.conn.execute(
            """INSERT INTO review_history (ku_id, session_turn_id, quality,
               easiness_factor_before, easiness_factor_after,
               interval_before, interval_after)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ku_id, session_turn_id, quality, ef_before, ef_after,
             interval_before, interval_after),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_review_history(self, ku_id: int) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM review_history WHERE ku_id = ? ORDER BY reviewed_at",
            (ku_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Streaks ---

    def record_study_day(
        self,
        study_date: date,
        sessions_count: int,
        total_minutes: int,
    ) -> None:
        yesterday = study_date - timedelta(days=1)
        prev = self.conn.execute(
            "SELECT current_streak, longest_streak FROM streaks WHERE date = ?",
            (yesterday.isoformat(),),
        ).fetchone()

        if prev:
            current = prev["current_streak"] + 1
            longest = max(prev["longest_streak"], current)
        else:
            current = 1
            longest = 1

        # Check if longest_streak should carry forward from any previous record
        max_longest = self.conn.execute(
            "SELECT MAX(longest_streak) as m FROM streaks"
        ).fetchone()
        if max_longest and max_longest["m"] and max_longest["m"] > longest:
            longest = max_longest["m"]

        self.conn.execute(
            """INSERT INTO streaks (date, sessions_count, total_minutes,
               current_streak, longest_streak)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(date) DO UPDATE SET
               sessions_count = sessions_count + excluded.sessions_count,
               total_minutes = total_minutes + excluded.total_minutes,
               current_streak = excluded.current_streak,
               longest_streak = excluded.longest_streak""",
            (study_date.isoformat(), sessions_count, total_minutes, current, longest),
        )
        self.conn.commit()

    def get_streak_info(self) -> dict[str, Any]:
        row = self.conn.execute(
            "SELECT * FROM streaks ORDER BY date DESC LIMIT 1"
        ).fetchone()
        if row:
            return dict(row)
        return {"current_streak": 0, "longest_streak": 0}
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_db.py -v`
Expected: All tests PASS

- [ ] **Step 8: Commit**

```bash
git add backend/memoryforge/db/ backend/tests/test_db.py
git commit -m "feat: database layer with schema, connection manager, and repository"
```

---

## Task 3: SM-2 Engine

**Files:**
- Create: `backend/memoryforge/sm2/__init__.py`
- Create: `backend/memoryforge/sm2/engine.py`
- Create: `backend/tests/test_sm2.py`

- [ ] **Step 1: Write failing SM-2 tests**

```python
"""Tests for the SM-2 spaced repetition algorithm."""

from memoryforge.sm2.engine import sm2, SM2State, quality_from_grade


class TestSM2Algorithm:
    def test_first_correct_review(self):
        state = SM2State()
        new_state = sm2(quality=4, state=state)
        assert new_state.repetitions == 1
        assert new_state.interval == 1
        assert new_state.easiness_factor >= 2.4

    def test_second_correct_review(self):
        state = SM2State(repetitions=1, interval=1, easiness_factor=2.5)
        new_state = sm2(quality=4, state=state)
        assert new_state.repetitions == 2
        assert new_state.interval == 6

    def test_third_correct_review(self):
        state = SM2State(repetitions=2, interval=6, easiness_factor=2.5)
        new_state = sm2(quality=5, state=state)
        assert new_state.repetitions == 3
        assert new_state.interval == 15  # round(6 * 2.5)

    def test_incorrect_resets_repetitions(self):
        state = SM2State(repetitions=5, interval=30, easiness_factor=2.5)
        new_state = sm2(quality=1, state=state)
        assert new_state.repetitions == 0
        assert new_state.interval == 1

    def test_easiness_factor_never_below_minimum(self):
        state = SM2State(easiness_factor=1.3)
        new_state = sm2(quality=0, state=state)
        assert new_state.easiness_factor >= 1.3

    def test_perfect_score_increases_ef(self):
        state = SM2State(easiness_factor=2.5)
        new_state = sm2(quality=5, state=state)
        assert new_state.easiness_factor == 2.6

    def test_quality_3_barely_correct(self):
        state = SM2State(easiness_factor=2.5)
        new_state = sm2(quality=3, state=state)
        assert new_state.easiness_factor == 2.36

    def test_quality_0_blackout(self):
        state = SM2State(easiness_factor=2.5)
        new_state = sm2(quality=0, state=state)
        assert new_state.repetitions == 0
        assert new_state.interval == 1
        # EF decreases but stays >= 1.3
        assert new_state.easiness_factor == 1.7

    def test_default_state(self):
        state = SM2State()
        assert state.repetitions == 0
        assert state.interval == 0
        assert state.easiness_factor == 2.5

    def test_long_term_interval_growth(self):
        """Simulate multiple perfect reviews to verify interval growth."""
        state = SM2State()
        intervals = []
        for _ in range(6):
            state = sm2(quality=5, state=state)
            intervals.append(state.interval)
        # Intervals should grow: 1, 6, 16, 42, 109, 283 (approximately)
        assert intervals[0] == 1
        assert intervals[1] == 6
        for i in range(2, len(intervals)):
            assert intervals[i] > intervals[i - 1]


class TestQualityMapping:
    def test_grade_5_maps_to_5(self):
        assert quality_from_grade(5) == 5

    def test_grade_0_maps_to_0(self):
        assert quality_from_grade(0) == 0

    def test_grade_out_of_range_clamps(self):
        assert quality_from_grade(7) == 5
        assert quality_from_grade(-1) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_sm2.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create sm2/__init__.py**

```python
"""SM-2 spaced repetition algorithm."""
```

- [ ] **Step 4: Create sm2/engine.py**

```python
"""Pure SM-2 algorithm implementation.

No external dependencies. No Claude. No network. Fully deterministic.
Based on the SuperMemo SM-2 algorithm by Piotr Wozniak.
"""

from dataclasses import dataclass


MIN_EASINESS_FACTOR = 1.3
DEFAULT_EASINESS_FACTOR = 2.5


@dataclass
class SM2State:
    """Current SM-2 scheduling state for a knowledge unit."""

    repetitions: int = 0
    interval: int = 0
    easiness_factor: float = DEFAULT_EASINESS_FACTOR


def sm2(quality: int, state: SM2State) -> SM2State:
    """Run one SM-2 review cycle.

    Args:
        quality: 0-5 rating of recall quality.
            5=perfect, 4=hesitation, 3=difficult, 2=incorrect but recognized,
            1=incorrect vaguely remembered, 0=blackout.
        state: Current SM-2 state.

    Returns:
        New SM2State with updated values.
    """
    repetitions = state.repetitions
    interval = state.interval
    ef = state.easiness_factor

    if quality >= 3:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * ef)
        repetitions += 1
    else:
        repetitions = 0
        interval = 1

    ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ef = max(MIN_EASINESS_FACTOR, ef)

    return SM2State(
        repetitions=repetitions,
        interval=interval,
        easiness_factor=round(ef, 2),
    )


def quality_from_grade(grade: int) -> int:
    """Clamp a grade value to the valid 0-5 SM-2 quality range."""
    return max(0, min(5, grade))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_sm2.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add backend/memoryforge/sm2/ backend/tests/test_sm2.py
git commit -m "feat: SM-2 spaced repetition engine with pure Python implementation"
```

---

## Task 4: Material Parsers

**Files:**
- Create: `backend/memoryforge/parser/__init__.py`
- Create: `backend/memoryforge/parser/pdf_parser.py`
- Create: `backend/memoryforge/parser/docx_parser.py`
- Create: `backend/memoryforge/parser/text_parser.py`
- Create: `backend/tests/test_parser.py`

- [ ] **Step 1: Write failing parser tests**

```python
"""Tests for material parsers."""

from pathlib import Path

from memoryforge.parser.text_parser import parse_text, parse_markdown
from memoryforge.parser.pdf_parser import parse_pdf
from memoryforge.parser.docx_parser import parse_docx


class TestTextParser:
    def test_parse_plain_text(self, tmp_path: Path):
        f = tmp_path / "notes.txt"
        f.write_text("Chapter 1: Cells\n\nCells are the basic unit of life.\n\nChapter 2: DNA\n\nDNA stores genetic information.")
        result = parse_text(f)
        assert result.text is not None
        assert "Cells" in result.text
        assert result.page_count is None

    def test_parse_markdown(self, tmp_path: Path):
        f = tmp_path / "notes.md"
        f.write_text("# Chapter 1: Cells\n\nCells are the basic unit of life.\n\n# Chapter 2: DNA\n\nDNA stores genetic information.")
        result = parse_markdown(f)
        assert len(result.sections) == 2
        assert result.sections[0]["heading"] == "Chapter 1: Cells"

    def test_empty_file(self, tmp_path: Path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        result = parse_text(f)
        assert result.text == ""


class TestPdfParser:
    def test_parse_pdf_returns_text(self, tmp_path: Path):
        """Integration test — requires pymupdf to create a test PDF."""
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Chapter 1: Introduction\n\nThis is the introduction.")
        pdf_path = tmp_path / "test.pdf"
        doc.save(str(pdf_path))
        doc.close()

        result = parse_pdf(pdf_path)
        assert result.page_count == 1
        assert "Introduction" in result.text

    def test_parse_pdf_structure(self, tmp_path: Path):
        import fitz
        doc = fitz.open()
        for i in range(3):
            page = doc.new_page()
            page.insert_text((72, 72), f"Page {i + 1} content")
        pdf_path = tmp_path / "multi.pdf"
        doc.save(str(pdf_path))
        doc.close()

        result = parse_pdf(pdf_path)
        assert result.page_count == 3


class TestDocxParser:
    def test_parse_docx(self, tmp_path: Path):
        from docx import Document
        doc = Document()
        doc.add_heading("Chapter 1: Cells", level=1)
        doc.add_paragraph("Cells are the basic unit of life.")
        doc.add_heading("Chapter 2: DNA", level=1)
        doc.add_paragraph("DNA stores genetic information.")
        docx_path = tmp_path / "test.docx"
        doc.save(str(docx_path))

        result = parse_docx(docx_path)
        assert "Cells" in result.text
        assert len(result.sections) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_parser.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create parser/__init__.py**

```python
"""Material parsing for uploaded documents."""

from dataclasses import dataclass, field


@dataclass
class ParseResult:
    """Result of parsing a document."""

    text: str
    page_count: int | None = None
    sections: list[dict] = field(default_factory=list)
```

- [ ] **Step 4: Create text_parser.py**

```python
"""Plain text and markdown parser."""

import re
from pathlib import Path

from memoryforge.parser import ParseResult


def parse_text(file_path: Path) -> ParseResult:
    """Parse a plain text file."""
    text = file_path.read_text(encoding="utf-8")
    return ParseResult(text=text)


def parse_markdown(file_path: Path) -> ParseResult:
    """Parse a markdown file, extracting heading-based sections."""
    text = file_path.read_text(encoding="utf-8")
    sections = []
    current_heading = None
    current_body_lines: list[str] = []

    for line in text.split("\n"):
        match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if match:
            if current_heading is not None:
                sections.append({
                    "heading": current_heading,
                    "body": "\n".join(current_body_lines).strip(),
                })
            current_heading = match.group(2)
            current_body_lines = []
        else:
            current_body_lines.append(line)

    if current_heading is not None:
        sections.append({
            "heading": current_heading,
            "body": "\n".join(current_body_lines).strip(),
        })

    return ParseResult(text=text, sections=sections)
```

- [ ] **Step 5: Create pdf_parser.py**

```python
"""PDF parser using pymupdf (fitz)."""

from pathlib import Path

import fitz

from memoryforge.parser import ParseResult


def parse_pdf(file_path: Path) -> ParseResult:
    """Extract text and structure from a PDF file."""
    doc = fitz.open(str(file_path))
    pages_text = []
    sections = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        pages_text.append(text)

    doc.close()

    full_text = "\n\n".join(pages_text)
    return ParseResult(
        text=full_text,
        page_count=len(pages_text),
        sections=sections,
    )
```

- [ ] **Step 6: Create docx_parser.py**

```python
"""DOCX parser using python-docx."""

from pathlib import Path

from docx import Document

from memoryforge.parser import ParseResult


def parse_docx(file_path: Path) -> ParseResult:
    """Extract text and heading-based sections from a DOCX file."""
    doc = Document(str(file_path))
    sections = []
    full_text_parts = []
    current_heading = None
    current_body_lines: list[str] = []

    for para in doc.paragraphs:
        full_text_parts.append(para.text)

        if para.style and para.style.name.startswith("Heading"):
            if current_heading is not None:
                sections.append({
                    "heading": current_heading,
                    "body": "\n".join(current_body_lines).strip(),
                })
            current_heading = para.text
            current_body_lines = []
        else:
            current_body_lines.append(para.text)

    if current_heading is not None:
        sections.append({
            "heading": current_heading,
            "body": "\n".join(current_body_lines).strip(),
        })

    return ParseResult(
        text="\n".join(full_text_parts),
        sections=sections,
    )
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_parser.py -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add backend/memoryforge/parser/ backend/tests/test_parser.py
git commit -m "feat: material parsers for PDF, DOCX, and plain text/markdown"
```

---

## Task 5: Claude Service + 3-Layer Pattern

**Files:**
- Create: `backend/memoryforge/claude_service/__init__.py`
- Create: `backend/memoryforge/claude_service/client.py`
- Create: `backend/memoryforge/claude_service/prompts.py`
- Create: `backend/memoryforge/claude_service/three_layer.py`
- Create: `backend/tests/test_claude_service.py`

- [ ] **Step 1: Write tests (with mock Claude responses)**

```python
"""Tests for the Claude service layer.

These tests mock the Claude agent-sdk to test prompt construction
and response handling without making real API calls.
"""

from unittest.mock import AsyncMock, patch, MagicMock
import json

from memoryforge.claude_service.prompts import (
    build_ku_extraction_prompt,
    build_quiz_prompt,
    build_grading_prompt,
    build_lesson_prompt,
    build_reteach_prompt,
    build_generative_probe_prompt,
    build_learning_plan_prompt,
)
from memoryforge.claude_service.three_layer import (
    build_summary_context,
    build_expanded_context,
)


class TestPromptConstruction:
    def test_ku_extraction_prompt_includes_text(self):
        prompt = build_ku_extraction_prompt(
            text_chunk="Mitochondria are the powerhouse of the cell.",
            subject_name="BIO 301",
            section_heading="Chapter 5: Cell Organelles",
        )
        assert "Mitochondria" in prompt
        assert "BIO 301" in prompt
        assert "Chapter 5" in prompt
        assert "JSON" in prompt  # Should request structured output

    def test_quiz_prompt_includes_concept(self):
        prompt = build_quiz_prompt(
            concept="Mitochondria produce ATP via oxidative phosphorylation",
            concept_summary="Mitochondria: ATP production",
            question_format="free_response",
            difficulty=3,
            previous_questions=["What organelle produces ATP?"],
        )
        assert "oxidative phosphorylation" in prompt
        assert "free_response" in prompt

    def test_quiz_prompt_varies_with_format(self):
        fr = build_quiz_prompt(
            concept="X", concept_summary="X",
            question_format="free_response", difficulty=3,
        )
        mc = build_quiz_prompt(
            concept="X", concept_summary="X",
            question_format="multiple_choice", difficulty=3,
        )
        assert fr != mc

    def test_grading_prompt_includes_answer(self):
        prompt = build_grading_prompt(
            question="What do mitochondria produce?",
            student_answer="They make ATP",
            concept="Mitochondria produce ATP via oxidative phosphorylation",
            strictness=2,
        )
        assert "They make ATP" in prompt
        assert "strictness" in prompt.lower() or "moderate" in prompt.lower()

    def test_lesson_prompt(self):
        prompt = build_lesson_prompt(
            concept="Mitochondria produce ATP",
            concept_summary="Mitochondria: ATP production",
            student_context="Student previously learned about cell membranes.",
        )
        assert "Mitochondria" in prompt
        assert "cell membranes" in prompt

    def test_reteach_prompt_socratic(self):
        prompt = build_reteach_prompt(
            concept="Mitochondria produce ATP",
            student_answer="I don't know",
            question="What do mitochondria produce?",
            attempt_number=1,
        )
        assert "guiding question" in prompt.lower() or "socratic" in prompt.lower()

    def test_reteach_prompt_direct_after_attempts(self):
        prompt = build_reteach_prompt(
            concept="Mitochondria produce ATP",
            student_answer="Still not sure",
            question="What do mitochondria produce?",
            attempt_number=3,
        )
        assert "explain" in prompt.lower() or "direct" in prompt.lower()

    def test_generative_probe_prompt(self):
        prompt = build_generative_probe_prompt(
            topic="Photosynthesis",
            subject_name="BIO 301",
            student_knowledge_summary="Has studied cell biology and respiration.",
        )
        assert "Photosynthesis" in prompt
        assert "think" in prompt.lower() or "predict" in prompt.lower()

    def test_learning_plan_prompt(self):
        prompt = build_learning_plan_prompt(
            subject_name="BIO 301",
            material_outline='["Cell Biology", "Genetics", "Evolution"]',
            current_progress='{"Cell Biology": 0.8, "Genetics": 0.2}',
            deadlines='{"midterm": "2026-05-01"}',
        )
        assert "BIO 301" in prompt
        assert "midterm" in prompt


class TestThreeLayerPattern:
    def test_build_summary_context(self):
        kus = [
            {"id": 1, "concept_summary": "Mitochondria: ATP", "difficulty": 3, "easiness_factor": 2.5, "repetitions": 3},
            {"id": 2, "concept_summary": "Cell membrane: selective permeability", "difficulty": 2, "easiness_factor": 2.1, "repetitions": 1},
        ]
        summary = build_summary_context(kus)
        assert "Mitochondria" in summary
        assert "Cell membrane" in summary
        # Should be compact — no full concept text
        assert len(summary) < 500

    def test_build_expanded_context(self):
        kus = [
            {"id": 1, "concept": "Mitochondria produce ATP via oxidative phosphorylation", "concept_summary": "Mitochondria: ATP", "tags": '["biology"]', "difficulty": 3},
        ]
        reviews = [
            {"quality": 4, "reviewed_at": "2026-04-10"},
            {"quality": 2, "reviewed_at": "2026-04-12"},
        ]
        expanded = build_expanded_context(kus, {1: reviews})
        assert "oxidative phosphorylation" in expanded
        assert "quality" in expanded.lower() or "review" in expanded.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_claude_service.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create claude_service/__init__.py**

```python
"""Claude AI service for MemoryForge."""
```

- [ ] **Step 4: Create prompts.py**

```python
"""All prompt templates for Claude interactions.

Central location for every prompt MemoryForge sends to Claude.
Keeps prompt engineering separate from business logic.
"""


def build_ku_extraction_prompt(
    text_chunk: str,
    subject_name: str,
    section_heading: str | None = None,
) -> str:
    heading_ctx = f"\nSection: {section_heading}" if section_heading else ""
    return f"""You are an expert educator analyzing study material for the subject "{subject_name}".{heading_ctx}

Extract distinct knowledge units (concepts) from the following text. Each knowledge unit should represent one testable concept.

For each knowledge unit, provide:
- concept: A clear, complete statement of the concept (1-3 sentences)
- concept_summary: A brief label (under 10 words) for quick reference
- difficulty: 1-5 rating (1=basic definition, 5=complex synthesis)
- tags: Relevant topic tags as a list
- prerequisites: List of concept_summaries this depends on (from this batch or general knowledge)

Return valid JSON array. Example format:
[
  {{
    "concept": "Mitochondria produce ATP through oxidative phosphorylation...",
    "concept_summary": "Mitochondria: ATP production",
    "difficulty": 3,
    "tags": ["cell-biology", "organelles", "energy"],
    "prerequisites": ["Cell structure basics"]
  }}
]

Text to analyze:
{text_chunk}"""


def build_quiz_prompt(
    concept: str,
    concept_summary: str,
    question_format: str,
    difficulty: int,
    previous_questions: list[str] | None = None,
) -> str:
    prev_ctx = ""
    if previous_questions:
        prev_list = "\n".join(f"- {q}" for q in previous_questions[-3:])
        prev_ctx = f"\n\nPrevious questions asked about this concept (DO NOT repeat these):\n{prev_list}"

    format_instructions = {
        "free_response": "Ask an open-ended question requiring a written explanation. The student should demonstrate understanding, not just recall a definition.",
        "multiple_choice": "Create a multiple-choice question with 4 options (A-D). Include one correct answer and three plausible distractors. Indicate the correct answer.",
        "fill_in_blank": "Create a sentence with a key term or phrase blanked out. The blank should test understanding of the core concept.",
        "apply_the_concept": "Present a novel scenario or problem that requires applying this concept. The student must use the concept to analyze or solve something new.",
    }

    return f"""Generate a {question_format} question about the following concept.

Concept: {concept}
Difficulty level: {difficulty}/5
Format: {format_instructions.get(question_format, format_instructions["free_response"])}
{prev_ctx}

Generate a fresh, unique question. Vary your angle — test different aspects of understanding each time.

Return JSON:
{{
  "question": "...",
  "expected_answer": "...",
  "format": "{question_format}"
}}"""


def build_grading_prompt(
    question: str,
    student_answer: str,
    concept: str,
    strictness: int,
) -> str:
    strictness_desc = {
        1: "Lenient — accept answers that show general understanding even if imprecise or missing details",
        2: "Moderate — the answer should be substantially correct with key details present",
        3: "Strict — the answer must be precise and complete, covering all essential aspects",
    }
    return f"""Grade this student's answer.

Question: {question}
Student's answer: {student_answer}
Correct concept: {concept}
Grading strictness: {strictness_desc.get(strictness, strictness_desc[2])}

Evaluate whether the student demonstrates understanding of the concept.

Return JSON:
{{
  "quality": <0-5 integer, where 5=perfect, 4=correct with hesitation, 3=correct but difficult, 2=incorrect but close, 1=incorrect, 0=no understanding>,
  "feedback": "<brief, encouraging feedback explaining what was right/wrong>",
  "correct": <true/false>
}}"""


def build_lesson_prompt(
    concept: str,
    concept_summary: str,
    student_context: str | None = None,
) -> str:
    ctx = ""
    if student_context:
        ctx = f"\n\nStudent context (what they already know): {student_context}"
    return f"""You are a patient, encouraging tutor. Teach the following concept clearly and concisely.{ctx}

Concept to teach: {concept}
Topic: {concept_summary}

Instructions:
- Explain the concept in clear, accessible language
- Use an analogy or real-world example if helpful
- Connect to concepts the student already knows (if context provided)
- End with an elaboration prompt — ask the student how this connects to something they've previously learned
- Keep it under 200 words"""


def build_reteach_prompt(
    concept: str,
    student_answer: str,
    question: str,
    attempt_number: int,
) -> str:
    if attempt_number <= 2:
        approach = """Use the Socratic method:
- Ask a guiding question that leads the student toward the answer
- Don't give the answer directly
- Build on what the student DID know (if anything)
- Keep it to one question"""
    else:
        approach = """The student has struggled through multiple attempts. Now explain directly:
- Give a clear, direct explanation of the concept
- Use a different analogy or framing than before
- Break it into smaller pieces
- End with an elaboration prompt to check understanding"""

    return f"""A student is struggling with this concept. Help them learn it.

Question that was asked: {question}
Student's answer: {student_answer}
Correct concept: {concept}
Attempt number: {attempt_number}

{approach}"""


def build_generative_probe_prompt(
    topic: str,
    subject_name: str,
    student_knowledge_summary: str | None = None,
) -> str:
    ctx = ""
    if student_knowledge_summary:
        ctx = f"\n\nWhat the student already knows: {student_knowledge_summary}"
    return f"""You are a tutor about to introduce a new topic in {subject_name}.

Before teaching, you want to activate the student's prior knowledge and create cognitive hooks (generation effect).

New topic to introduce: {topic}
{ctx}

Ask ONE thought-provoking question that:
- Makes the student think about and predict something related to this topic
- Can be answered with reasoning even without formal knowledge
- Creates curiosity about the upcoming concept
- Is open-ended (no single correct answer)

Don't tell the student they're about to learn this topic. Just ask the question naturally.

Return JSON:
{{
  "probe_question": "...",
  "topic_connection": "brief note on how this connects to what you'll teach"
}}"""


def build_learning_plan_prompt(
    subject_name: str,
    material_outline: str,
    current_progress: str,
    deadlines: str,
) -> str:
    return f"""Create a learning plan for the subject "{subject_name}".

Available material topics: {material_outline}
Current progress (topic: mastery 0.0-1.0): {current_progress}
Deadlines: {deadlines}

Create an ordered study plan that:
- Prioritizes topics with upcoming deadlines
- Respects prerequisite dependencies
- Focuses on weak areas (low mastery)
- Introduces new topics at a sustainable pace
- Spaces review of mastered topics appropriately

Return JSON:
{{
  "ordered_topics": ["topic1", "topic2", ...],
  "milestones": [{{"topic": "...", "target_date": "YYYY-MM-DD", "reason": "..."}}],
  "focus_areas": ["topic with low mastery", ...],
  "daily_new_concepts": <recommended number of new concepts per day>
}}"""
```

- [ ] **Step 5: Create three_layer.py**

```python
"""3-layer token-efficiency pattern for Claude interactions.

Inspired by claude-mem's search pattern:
1. Summary layer — compact KU descriptions for broad context
2. Expanded layer — full details for selected KUs
3. Generation layer — Claude produces content with focused context

This keeps token usage manageable across large course loads.
"""

import json


def build_summary_context(kus: list[dict]) -> str:
    """Layer 1: Build a compact summary of KUs for broad context.

    Used when Claude needs awareness of many KUs but doesn't need
    full details on each one. ~20-30 tokens per KU.
    """
    lines = []
    for ku in kus:
        ef = ku.get("easiness_factor", 2.5)
        reps = ku.get("repetitions", 0)
        diff = ku.get("difficulty", 3)
        mastery = "new" if reps == 0 else f"reps:{reps},ef:{ef:.1f}"
        lines.append(f"[KU#{ku['id']}] {ku['concept_summary']} (d:{diff},{mastery})")
    return "\n".join(lines)


def build_expanded_context(
    kus: list[dict],
    review_histories: dict[int, list[dict]],
) -> str:
    """Layer 2: Expand selected KUs with full concept and review history.

    Used after layer 1 identifies which KUs need attention.
    """
    parts = []
    for ku in kus:
        ku_id = ku["id"]
        reviews = review_histories.get(ku_id, [])
        review_summary = ""
        if reviews:
            recent = reviews[-3:]  # Last 3 reviews
            review_lines = [
                f"  - quality:{r['quality']} on {r['reviewed_at']}"
                for r in recent
            ]
            review_summary = "\nRecent reviews:\n" + "\n".join(review_lines)

        tags = ku.get("tags", "[]")
        if isinstance(tags, str):
            tags = json.loads(tags)

        parts.append(
            f"[KU#{ku_id}] {ku['concept']}\n"
            f"Tags: {', '.join(tags)}\n"
            f"Difficulty: {ku.get('difficulty', 3)}/5"
            f"{review_summary}"
        )
    return "\n\n".join(parts)
```

- [ ] **Step 6: Create client.py**

```python
"""Claude agent-sdk wrapper for MemoryForge.

Handles all communication with Claude through the agent SDK.
All prompts come from prompts.py — this module only handles
sending/receiving and parsing responses.
"""

import json
from typing import Any


async def query_claude(prompt: str) -> str:
    """Send a prompt to Claude and return the text response.

    Uses claude-agent-sdk's query() function.
    Falls back gracefully if the SDK is not available.
    """
    try:
        from claude_agent_sdk import query as agent_query
    except ImportError:
        raise RuntimeError(
            "claude-agent-sdk is not installed. "
            "Install with: pip install claude-agent-sdk"
        )

    response_parts = []
    async for message in agent_query(prompt=prompt):
        if hasattr(message, "content"):
            response_parts.append(str(message.content))
        else:
            response_parts.append(str(message))

    return "".join(response_parts)


async def query_claude_json(prompt: str) -> dict[str, Any]:
    """Send a prompt and parse the JSON response."""
    raw = await query_claude(prompt)

    # Extract JSON from response — Claude may wrap it in markdown code blocks
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (```json and ```)
        text = "\n".join(lines[1:-1])

    return json.loads(text)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_claude_service.py -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add backend/memoryforge/claude_service/ backend/tests/test_claude_service.py
git commit -m "feat: Claude service with prompt templates and 3-layer token efficiency"
```

---

## Task 6: Question Type Registry

**Files:**
- Create: `backend/memoryforge/session/__init__.py`
- Create: `backend/memoryforge/session/question_registry.py`
- Create: `backend/tests/test_question_registry.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for the question type registry."""

from memoryforge.session.question_registry import (
    QuestionRegistry,
    get_question_format,
)


class TestQuestionRegistry:
    def test_default_formats_registered(self):
        registry = QuestionRegistry()
        formats = registry.list_formats()
        assert "free_response" in formats
        assert "multiple_choice" in formats
        assert "fill_in_blank" in formats
        assert "apply_the_concept" in formats

    def test_get_format_for_difficulty(self):
        registry = QuestionRegistry()
        # High difficulty concepts should prefer free_response or apply_the_concept
        fmt = registry.select_format(difficulty=5, quiz_format_pref="mixed")
        assert fmt in ("free_response", "apply_the_concept")

    def test_respects_user_preference(self):
        registry = QuestionRegistry()
        fmt = registry.select_format(difficulty=3, quiz_format_pref="multiple_choice")
        assert fmt == "multiple_choice"

    def test_mixed_varies_format(self):
        """Mixed mode should produce different formats across calls."""
        registry = QuestionRegistry()
        formats_seen = set()
        for d in range(1, 6):
            fmt = registry.select_format(difficulty=d, quiz_format_pref="mixed")
            formats_seen.add(fmt)
        # Should see at least 2 different formats across 5 difficulty levels
        assert len(formats_seen) >= 2

    def test_register_custom_format(self):
        registry = QuestionRegistry()
        registry.register("diagram", difficulty_range=(3, 5))
        assert "diagram" in registry.list_formats()

    def test_free_response_preference(self):
        registry = QuestionRegistry()
        fmt = registry.select_format(difficulty=3, quiz_format_pref="free_response")
        assert fmt == "free_response"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_question_registry.py -v`
Expected: FAIL

- [ ] **Step 3: Create session/__init__.py**

```python
"""Study session management."""
```

- [ ] **Step 4: Create question_registry.py**

```python
"""Pluggable question type registry.

The session engine asks "give me a question format for this KU"
and the registry handles selection based on difficulty, user
preference, and available formats.

New formats can be registered without changing the session engine.
"""

from dataclasses import dataclass


@dataclass
class QuestionFormat:
    """A registered question format."""

    name: str
    difficulty_range: tuple[int, int]  # (min, max) difficulty where this format applies


class QuestionRegistry:
    """Registry of available question formats."""

    def __init__(self) -> None:
        self._formats: dict[str, QuestionFormat] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register("free_response", difficulty_range=(1, 5))
        self.register("multiple_choice", difficulty_range=(1, 4))
        self.register("fill_in_blank", difficulty_range=(1, 3))
        self.register("apply_the_concept", difficulty_range=(3, 5))

    def register(self, name: str, difficulty_range: tuple[int, int] = (1, 5)) -> None:
        """Register a new question format."""
        self._formats[name] = QuestionFormat(name=name, difficulty_range=difficulty_range)

    def list_formats(self) -> list[str]:
        """Return all registered format names."""
        return list(self._formats.keys())

    def select_format(self, difficulty: int, quiz_format_pref: str) -> str:
        """Select a question format based on difficulty and user preference.

        If quiz_format_pref is a specific format, use that.
        If "mixed", select based on difficulty and variety.
        """
        if quiz_format_pref != "mixed" and quiz_format_pref in self._formats:
            return quiz_format_pref

        # Mixed mode: select based on difficulty
        eligible = [
            name for name, fmt in self._formats.items()
            if fmt.difficulty_range[0] <= difficulty <= fmt.difficulty_range[1]
        ]

        if not eligible:
            return "free_response"

        # Prefer harder formats for harder concepts
        if difficulty >= 4:
            for preferred in ("apply_the_concept", "free_response"):
                if preferred in eligible:
                    return preferred
        elif difficulty <= 2:
            for preferred in ("fill_in_blank", "multiple_choice"):
                if preferred in eligible:
                    return preferred

        return eligible[0]


def get_question_format(
    difficulty: int,
    quiz_format_pref: str,
    registry: QuestionRegistry | None = None,
) -> str:
    """Convenience function to get a question format."""
    if registry is None:
        registry = QuestionRegistry()
    return registry.select_format(difficulty, quiz_format_pref)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_question_registry.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add backend/memoryforge/session/ backend/tests/test_question_registry.py
git commit -m "feat: pluggable question type registry for quiz format selection"
```

---

## Task 7: Grader

**Files:**
- Create: `backend/memoryforge/session/grader.py`
- Create: `backend/tests/test_grader.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for the grading module."""

from unittest.mock import AsyncMock, patch

import pytest

from memoryforge.session.grader import grade_multiple_choice, GradeResult


class TestMultipleChoiceGrading:
    def test_correct_answer(self):
        result = grade_multiple_choice(
            student_answer="B",
            correct_answer="B",
        )
        assert result.correct is True
        assert result.quality == 5

    def test_incorrect_answer(self):
        result = grade_multiple_choice(
            student_answer="A",
            correct_answer="C",
        )
        assert result.correct is False
        assert result.quality == 0

    def test_case_insensitive(self):
        result = grade_multiple_choice(
            student_answer="b",
            correct_answer="B",
        )
        assert result.correct is True

    def test_feedback_on_correct(self):
        result = grade_multiple_choice(
            student_answer="B",
            correct_answer="B",
        )
        assert result.feedback is not None
        assert len(result.feedback) > 0

    def test_feedback_on_incorrect(self):
        result = grade_multiple_choice(
            student_answer="A",
            correct_answer="B",
        )
        assert "B" in result.feedback
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_grader.py -v`
Expected: FAIL

- [ ] **Step 3: Create grader.py**

```python
"""Grading logic for quiz responses.

Multiple choice: graded automatically (no Claude needed).
Free response / apply / fill-in-blank: graded by Claude via claude_service.
"""

from dataclasses import dataclass

from memoryforge.claude_service.prompts import build_grading_prompt
from memoryforge.claude_service.client import query_claude_json


@dataclass
class GradeResult:
    """Result of grading a student response."""

    quality: int  # 0-5 SM-2 scale
    correct: bool
    feedback: str


def grade_multiple_choice(
    student_answer: str,
    correct_answer: str,
) -> GradeResult:
    """Grade a multiple choice answer. No Claude needed."""
    is_correct = student_answer.strip().upper() == correct_answer.strip().upper()
    if is_correct:
        return GradeResult(
            quality=5,
            correct=True,
            feedback="Correct!",
        )
    return GradeResult(
        quality=0,
        correct=False,
        feedback=f"Incorrect. The correct answer was {correct_answer}.",
    )


async def grade_free_response(
    question: str,
    student_answer: str,
    concept: str,
    strictness: int,
) -> GradeResult:
    """Grade a free response answer using Claude."""
    prompt = build_grading_prompt(
        question=question,
        student_answer=student_answer,
        concept=concept,
        strictness=strictness,
    )
    result = await query_claude_json(prompt)
    return GradeResult(
        quality=result.get("quality", 0),
        correct=result.get("correct", False),
        feedback=result.get("feedback", ""),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_grader.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/memoryforge/session/grader.py backend/tests/test_grader.py
git commit -m "feat: grading module with auto MC grading and Claude-powered free response"
```

---

## Task 8: Context-Aware Scheduler

**Files:**
- Create: `backend/memoryforge/scheduler/__init__.py`
- Create: `backend/memoryforge/scheduler/context_aware.py`
- Create: `backend/tests/test_scheduler.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for the context-aware scheduler."""

import json
from datetime import date

from memoryforge.scheduler.context_aware import (
    build_session_queue,
    SessionQueueItem,
)


def _make_ku(
    ku_id: int,
    subject_id: int,
    concept_summary: str,
    difficulty: int = 3,
    tags: str = "[]",
    prerequisites: str = "[]",
    repetitions: int = 0,
    next_review: str | None = None,
) -> dict:
    return {
        "id": ku_id,
        "subject_id": subject_id,
        "concept": f"Full concept for {concept_summary}",
        "concept_summary": concept_summary,
        "difficulty": difficulty,
        "tags": tags,
        "prerequisites": prerequisites,
        "easiness_factor": 2.5,
        "interval": 0,
        "repetitions": repetitions,
        "next_review": next_review,
    }


class TestBuildSessionQueue:
    def test_empty_due_list(self):
        queue = build_session_queue(
            due_kus=[],
            new_topics=[],
            interleave_ratio=0.3,
        )
        assert queue == []

    def test_single_subject_clusters(self):
        kus = [
            _make_ku(1, 1, "Cell membrane", tags='["bio", "cells"]'),
            _make_ku(2, 1, "Cell wall", tags='["bio", "cells"]'),
            _make_ku(3, 1, "Nucleus", tags='["bio", "cells"]'),
        ]
        queue = build_session_queue(
            due_kus=kus,
            new_topics=[],
            interleave_ratio=0.3,
        )
        assert len(queue) == 3
        # All should be quiz type since they're review KUs
        assert all(item.activity_type == "quiz" for item in queue)

    def test_interleaving_two_subjects(self):
        kus = [
            _make_ku(1, 1, "Cell membrane", tags='["bio"]'),
            _make_ku(2, 1, "Cell wall", tags='["bio"]'),
            _make_ku(3, 1, "Nucleus", tags='["bio"]'),
            _make_ku(4, 2, "French Revolution", tags='["history"]'),
            _make_ku(5, 2, "Napoleon", tags='["history"]'),
        ]
        queue = build_session_queue(
            due_kus=kus,
            new_topics=[],
            interleave_ratio=0.3,
        )
        assert len(queue) == 5
        # Should not be all subject_id=1 followed by all subject_id=2
        subject_ids = [item.ku["subject_id"] for item in queue]
        # With interleaving, subjects should be mixed
        switches = sum(1 for i in range(1, len(subject_ids)) if subject_ids[i] != subject_ids[i - 1])
        assert switches >= 1

    def test_new_topics_get_probes_and_lessons(self):
        new_topics = [
            {"topic": "Photosynthesis", "subject_id": 1, "subject_name": "BIO 301"},
        ]
        queue = build_session_queue(
            due_kus=[],
            new_topics=new_topics,
            interleave_ratio=0.3,
        )
        types = [item.activity_type for item in queue]
        assert "generative_probe" in types
        assert "lesson" in types

    def test_prerequisites_respected(self):
        kus = [
            _make_ku(1, 1, "Addition", prerequisites="[]"),
            _make_ku(2, 1, "Multiplication", prerequisites="[1]"),
        ]
        queue = build_session_queue(
            due_kus=kus,
            new_topics=[],
            interleave_ratio=0.0,
        )
        ku_order = [item.ku["id"] for item in queue if item.ku is not None]
        idx_1 = ku_order.index(1)
        idx_2 = ku_order.index(2)
        assert idx_1 < idx_2

    def test_long_term_review_included(self):
        kus = [
            _make_ku(1, 1, "Old concept", repetitions=10, next_review="2026-01-01"),
            _make_ku(2, 1, "Recent concept", repetitions=1, next_review="2026-04-12"),
        ]
        queue = build_session_queue(
            due_kus=kus,
            new_topics=[],
            interleave_ratio=0.0,
        )
        assert len(queue) == 2


class TestSessionQueueItem:
    def test_quiz_item(self):
        ku = _make_ku(1, 1, "Test concept")
        item = SessionQueueItem(activity_type="quiz", ku=ku)
        assert item.activity_type == "quiz"
        assert item.ku["id"] == 1

    def test_probe_item(self):
        item = SessionQueueItem(
            activity_type="generative_probe",
            ku=None,
            topic_info={"topic": "Photosynthesis", "subject_id": 1},
        )
        assert item.activity_type == "generative_probe"
        assert item.ku is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_scheduler.py -v`
Expected: FAIL

- [ ] **Step 3: Create scheduler/__init__.py**

```python
"""Context-aware scheduling for study sessions."""
```

- [ ] **Step 4: Create context_aware.py**

```python
"""Context-aware session queue builder.

SM-2 answers "what's due?" — this module answers "in what order and grouping?"

Scheduling strategy:
1. Cluster 2-3 related KUs from the same subject (connection-building)
2. Insert subject switches for interleaving
3. Place generative probes before new topic lessons
4. Place long-term review cards in gaps between clusters
5. Respect prerequisite ordering
"""

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionQueueItem:
    """One item in the session queue."""

    activity_type: str  # "quiz", "lesson", "generative_probe", "reteach"
    ku: dict | None = None
    topic_info: dict | None = None


def build_session_queue(
    due_kus: list[dict],
    new_topics: list[dict],
    interleave_ratio: float = 0.3,
    cluster_size: int = 3,
) -> list[SessionQueueItem]:
    """Build an ordered session queue from due KUs and new topics.

    Args:
        due_kus: KUs where next_review <= today, from repository.
        new_topics: New topics ready to introduce (from learning plan).
        interleave_ratio: 0.0-1.0, how aggressively to mix subjects.
        cluster_size: How many related KUs to group together.

    Returns:
        Ordered list of SessionQueueItems.
    """
    if not due_kus and not new_topics:
        return []

    queue: list[SessionQueueItem] = []

    # Sort KUs respecting prerequisites
    ordered_kus = _topological_sort(due_kus)

    # Group by subject
    subject_groups: dict[int, list[dict]] = {}
    for ku in ordered_kus:
        sid = ku["subject_id"]
        subject_groups.setdefault(sid, []).append(ku)

    # Separate long-term review cards (high repetitions)
    long_term: list[dict] = []
    active: dict[int, list[dict]] = {}
    for sid, kus in subject_groups.items():
        active[sid] = []
        for ku in kus:
            if ku.get("repetitions", 0) >= 5:
                long_term.append(ku)
            else:
                active[sid].append(ku)

    # Build clusters from active KUs
    clusters: list[list[dict]] = []
    for sid, kus in active.items():
        for i in range(0, len(kus), cluster_size):
            clusters.append(kus[i:i + cluster_size])

    # Interleave clusters from different subjects
    if interleave_ratio > 0 and len(clusters) > 1:
        clusters = _interleave_clusters(clusters, interleave_ratio)

    # Add new topic probes + lessons before their subject clusters
    topics_added = set()
    for topic in new_topics:
        if topic["topic"] not in topics_added:
            queue.append(SessionQueueItem(
                activity_type="generative_probe",
                ku=None,
                topic_info=topic,
            ))
            queue.append(SessionQueueItem(
                activity_type="lesson",
                ku=None,
                topic_info=topic,
            ))
            topics_added.add(topic["topic"])

    # Add clustered quiz items
    for cluster in clusters:
        for ku in cluster:
            queue.append(SessionQueueItem(activity_type="quiz", ku=ku))

    # Sprinkle long-term review cards in gaps
    if long_term:
        _insert_long_term_reviews(queue, long_term)

    return queue


def _topological_sort(kus: list[dict]) -> list[dict]:
    """Sort KUs so prerequisites come before dependents."""
    ku_map = {ku["id"]: ku for ku in kus}
    visited: set[int] = set()
    result: list[dict] = []

    def visit(ku_id: int) -> None:
        if ku_id in visited or ku_id not in ku_map:
            return
        visited.add(ku_id)
        ku = ku_map[ku_id]
        prereqs = ku.get("prerequisites", "[]")
        if isinstance(prereqs, str):
            prereqs = json.loads(prereqs)
        for prereq_id in prereqs:
            visit(prereq_id)
        result.append(ku)

    for ku in kus:
        visit(ku["id"])

    return result


def _interleave_clusters(
    clusters: list[list[dict]],
    ratio: float,
) -> list[list[dict]]:
    """Reorder clusters to mix subjects based on interleave ratio.

    Higher ratio = more aggressive mixing.
    """
    if len(clusters) <= 1:
        return clusters

    # Group clusters by subject
    by_subject: dict[int, list[list[dict]]] = {}
    for cluster in clusters:
        sid = cluster[0]["subject_id"]
        by_subject.setdefault(sid, []).append(cluster)

    # Round-robin through subjects
    result: list[list[dict]] = []
    subject_ids = list(by_subject.keys())
    max_len = max(len(v) for v in by_subject.values())

    for i in range(max_len):
        for sid in subject_ids:
            if i < len(by_subject[sid]):
                result.append(by_subject[sid][i])

    return result


def _insert_long_term_reviews(
    queue: list[SessionQueueItem],
    long_term: list[dict],
) -> None:
    """Insert long-term review cards at regular intervals in the queue."""
    if not queue:
        for ku in long_term:
            queue.append(SessionQueueItem(activity_type="quiz", ku=ku))
        return

    # Insert one long-term card every N items
    spacing = max(3, len(queue) // (len(long_term) + 1))
    insert_positions = list(range(spacing, len(queue), spacing))

    for i, pos in enumerate(insert_positions):
        if i < len(long_term):
            adjusted_pos = min(pos + i, len(queue))
            queue.insert(
                adjusted_pos,
                SessionQueueItem(activity_type="quiz", ku=long_term[i]),
            )

    # Append any remaining long-term cards at the end
    for ku in long_term[len(insert_positions):]:
        queue.append(SessionQueueItem(activity_type="quiz", ku=ku))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_scheduler.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add backend/memoryforge/scheduler/ backend/tests/test_scheduler.py
git commit -m "feat: context-aware scheduler with clustering, interleaving, and prerequisites"
```

---

## Task 9: Session Engine

**Files:**
- Create: `backend/memoryforge/session/engine.py`
- Create: `backend/tests/test_session.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for the study session engine."""

from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from memoryforge.session.engine import SessionEngine
from memoryforge.scheduler.context_aware import SessionQueueItem


class TestSessionEngine:
    def test_start_session_creates_db_record(self, repo):
        engine = SessionEngine(repo=repo)
        session_id = engine.start_session()
        assert session_id >= 1
        session = repo.get_session(session_id)
        assert session is not None
        assert session["ended_at"] is None

    def test_get_next_turn_from_queue(self, repo):
        repo.create_subject(name="BIO 301")
        repo.create_material(
            subject_id=1, filename="ch1.pdf", file_path="/a",
            file_type="pdf", material_type="textbook",
        )
        repo.create_ku(
            subject_id=1, material_id=1,
            concept="Mitochondria produce ATP",
            concept_summary="Mitochondria: ATP",
            source_location="p102", difficulty=3,
            tags="[]", prerequisites="[]",
        )
        engine = SessionEngine(repo=repo)
        engine.start_session()

        ku = repo.get_ku(1)
        engine._queue = [SessionQueueItem(activity_type="quiz", ku=ku)]

        item = engine.get_next_item()
        assert item is not None
        assert item.activity_type == "quiz"

    def test_get_next_turn_returns_none_when_empty(self, repo):
        engine = SessionEngine(repo=repo)
        engine.start_session()
        engine._queue = []
        item = engine.get_next_item()
        assert item is None

    def test_record_quiz_turn(self, repo):
        repo.create_subject(name="BIO 301")
        repo.create_material(
            subject_id=1, filename="ch1.pdf", file_path="/a",
            file_type="pdf", material_type="textbook",
        )
        repo.create_ku(
            subject_id=1, material_id=1,
            concept="Mitochondria produce ATP",
            concept_summary="Mitochondria: ATP",
            source_location="p102", difficulty=3,
            tags="[]", prerequisites="[]",
        )
        engine = SessionEngine(repo=repo)
        session_id = engine.start_session()

        turn_id = engine.record_turn(
            ku_id=1,
            turn_type="quiz",
            question_text="What do mitochondria produce?",
            student_response="ATP",
            claude_feedback="Correct!",
            grade=5,
            time_taken_seconds=8,
        )
        assert turn_id >= 1
        turns = repo.get_session_turns(session_id)
        assert len(turns) == 1

    def test_record_turn_updates_sm2(self, repo):
        repo.create_subject(name="BIO 301")
        repo.create_material(
            subject_id=1, filename="ch1.pdf", file_path="/a",
            file_type="pdf", material_type="textbook",
        )
        repo.create_ku(
            subject_id=1, material_id=1,
            concept="Mitochondria produce ATP",
            concept_summary="Mitochondria: ATP",
            source_location="p102", difficulty=3,
            tags="[]", prerequisites="[]",
        )
        engine = SessionEngine(repo=repo)
        engine.start_session()
        engine.record_turn(
            ku_id=1, turn_type="quiz",
            question_text="Q?", student_response="A",
            claude_feedback="OK", grade=4,
            time_taken_seconds=10,
        )
        ku = repo.get_ku(1)
        assert ku["repetitions"] == 1
        assert ku["interval"] == 1
        assert ku["next_review"] is not None

    def test_end_session(self, repo):
        repo.create_subject(name="BIO 301")
        engine = SessionEngine(repo=repo)
        session_id = engine.start_session()
        summary = engine.end_session()
        assert summary["session_id"] == session_id
        session = repo.get_session(session_id)
        assert session["ended_at"] is not None

    def test_failed_quiz_triggers_reteach_flag(self, repo):
        repo.create_subject(name="BIO 301")
        repo.create_material(
            subject_id=1, filename="ch1.pdf", file_path="/a",
            file_type="pdf", material_type="textbook",
        )
        repo.create_ku(
            subject_id=1, material_id=1,
            concept="Mitochondria produce ATP",
            concept_summary="Mitochondria: ATP",
            source_location="p102", difficulty=3,
            tags="[]", prerequisites="[]",
        )
        engine = SessionEngine(repo=repo)
        engine.start_session()
        engine.record_turn(
            ku_id=1, turn_type="quiz",
            question_text="Q?", student_response="wrong",
            claude_feedback="Incorrect", grade=1,
            time_taken_seconds=10,
        )
        assert 1 in engine.needs_reteach
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_session.py -v`
Expected: FAIL

- [ ] **Step 3: Create engine.py**

```python
"""Study session orchestrator.

Manages the lifecycle of a study session: start, get next item,
record turns, update SM-2 state, track re-teach needs, end session.
"""

import json
from datetime import date, timedelta
from typing import Any

from memoryforge.db.repository import Repository
from memoryforge.sm2.engine import sm2, SM2State, quality_from_grade
from memoryforge.scheduler.context_aware import SessionQueueItem


class SessionEngine:
    """Orchestrates a single study session."""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo
        self.session_id: int | None = None
        self._queue: list[SessionQueueItem] = []
        self._subjects_seen: set[int] = set()
        self._correct: int = 0
        self._incorrect: int = 0
        self._skipped: int = 0
        self.needs_reteach: set[int] = set()  # KU IDs that need re-teaching

    def start_session(self) -> int:
        """Create a new session record and return its ID."""
        self.session_id = self.repo.create_session()
        return self.session_id

    def set_queue(self, queue: list[SessionQueueItem]) -> None:
        """Set the session queue (built by context-aware scheduler)."""
        self._queue = list(queue)

    def get_next_item(self) -> SessionQueueItem | None:
        """Pop and return the next item from the queue."""
        if not self._queue:
            return None
        return self._queue.pop(0)

    def record_turn(
        self,
        ku_id: int | None,
        turn_type: str,
        question_text: str,
        student_response: str | None,
        claude_feedback: str | None,
        grade: int | None,
        time_taken_seconds: int | None,
    ) -> int:
        """Record a session turn, update SM-2 state if graded."""
        turn_id = self.repo.create_session_turn(
            session_id=self.session_id,
            ku_id=ku_id,
            turn_type=turn_type,
            question_text=question_text,
            student_response=student_response,
            claude_feedback=claude_feedback,
            grade=grade,
            time_taken_seconds=time_taken_seconds,
        )

        # Update SM-2 state for graded quiz turns
        if ku_id is not None and grade is not None and turn_type == "quiz":
            ku = self.repo.get_ku(ku_id)
            if ku:
                self._subjects_seen.add(ku["subject_id"])
                quality = quality_from_grade(grade)

                old_state = SM2State(
                    repetitions=ku["repetitions"],
                    interval=ku["interval"],
                    easiness_factor=ku["easiness_factor"],
                )
                new_state = sm2(quality=quality, state=old_state)

                next_review = date.today() + timedelta(days=new_state.interval)
                self.repo.update_ku_sm2(
                    ku_id=ku_id,
                    easiness_factor=new_state.easiness_factor,
                    interval=new_state.interval,
                    repetitions=new_state.repetitions,
                    next_review=next_review,
                )

                self.repo.create_review(
                    ku_id=ku_id,
                    session_turn_id=turn_id,
                    quality=quality,
                    ef_before=old_state.easiness_factor,
                    ef_after=new_state.easiness_factor,
                    interval_before=old_state.interval,
                    interval_after=new_state.interval,
                )

                if quality >= 3:
                    self._correct += 1
                else:
                    self._incorrect += 1
                    self.needs_reteach.add(ku_id)

        # Track subjects for non-quiz turns too
        if ku_id is not None and turn_type != "quiz":
            ku = self.repo.get_ku(ku_id)
            if ku:
                self._subjects_seen.add(ku["subject_id"])

        return turn_id

    def end_session(self) -> dict[str, Any]:
        """End the session and return a summary."""
        score_summary = json.dumps({
            "correct": self._correct,
            "incorrect": self._incorrect,
            "skipped": self._skipped,
        })
        subjects_covered = json.dumps(list(self._subjects_seen))

        self.repo.end_session(
            session_id=self.session_id,
            subjects_covered=subjects_covered,
            score_summary=score_summary,
        )

        # Update streak
        self.repo.record_study_day(
            study_date=date.today(),
            sessions_count=1,
            total_minutes=0,  # Calculated from turn times in a future enhancement
        )

        return {
            "session_id": self.session_id,
            "correct": self._correct,
            "incorrect": self._incorrect,
            "skipped": self._skipped,
            "subjects_covered": list(self._subjects_seen),
            "needs_reteach": list(self.needs_reteach),
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_session.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/memoryforge/session/engine.py backend/tests/test_session.py
git commit -m "feat: session engine with SM-2 updates, re-teach tracking, and streak recording"
```

---

## Task 10: Streak Tracker

**Files:**
- Create: `backend/memoryforge/streak/__init__.py`
- Create: `backend/memoryforge/streak/tracker.py`
- Create: `backend/tests/test_streak.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for the streak tracker."""

from datetime import date

from memoryforge.streak.tracker import StreakTracker


class TestStreakTracker:
    def test_get_streak_no_history(self, repo):
        tracker = StreakTracker(repo=repo)
        info = tracker.get_info()
        assert info["current_streak"] == 0
        assert info["longest_streak"] == 0

    def test_single_day_streak(self, repo):
        tracker = StreakTracker(repo=repo)
        tracker.record_day(date(2026, 4, 13), sessions=1, minutes=30)
        info = tracker.get_info()
        assert info["current_streak"] == 1

    def test_multi_day_streak(self, repo):
        tracker = StreakTracker(repo=repo)
        tracker.record_day(date(2026, 4, 11), sessions=1, minutes=30)
        tracker.record_day(date(2026, 4, 12), sessions=1, minutes=30)
        tracker.record_day(date(2026, 4, 13), sessions=1, minutes=30)
        info = tracker.get_info()
        assert info["current_streak"] == 3
        assert info["longest_streak"] == 3

    def test_broken_streak(self, repo):
        tracker = StreakTracker(repo=repo)
        tracker.record_day(date(2026, 4, 10), sessions=1, minutes=30)
        # Skip April 11
        tracker.record_day(date(2026, 4, 12), sessions=1, minutes=30)
        tracker.record_day(date(2026, 4, 13), sessions=1, minutes=30)
        info = tracker.get_info()
        assert info["current_streak"] == 2
        assert info["longest_streak"] == 2

    def test_is_at_risk(self, repo):
        tracker = StreakTracker(repo=repo)
        tracker.record_day(date(2026, 4, 12), sessions=1, minutes=30)
        # If today is April 13 and no session yet, streak is at risk
        assert tracker.is_at_risk(today=date(2026, 4, 13)) is True

    def test_not_at_risk_if_studied_today(self, repo):
        tracker = StreakTracker(repo=repo)
        tracker.record_day(date(2026, 4, 13), sessions=1, minutes=30)
        assert tracker.is_at_risk(today=date(2026, 4, 13)) is False

    def test_not_at_risk_if_no_streak(self, repo):
        tracker = StreakTracker(repo=repo)
        assert tracker.is_at_risk(today=date(2026, 4, 13)) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_streak.py -v`
Expected: FAIL

- [ ] **Step 3: Create streak/__init__.py**

```python
"""Streak tracking for study motivation."""
```

- [ ] **Step 4: Create tracker.py**

```python
"""Streak tracker — Duolingo-inspired daily study streak.

Wraps the repository's streak methods with higher-level logic
for checking risk and computing stats.
"""

from datetime import date
from typing import Any

from memoryforge.db.repository import Repository


class StreakTracker:
    """Tracks daily study streaks."""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def record_day(self, study_date: date, sessions: int, minutes: int) -> None:
        """Record that studying happened on this date."""
        self.repo.record_study_day(
            study_date=study_date,
            sessions_count=sessions,
            total_minutes=minutes,
        )

    def get_info(self) -> dict[str, Any]:
        """Get current streak information."""
        return self.repo.get_streak_info()

    def is_at_risk(self, today: date) -> bool:
        """Check if the streak is at risk (studied yesterday but not today)."""
        info = self.get_info()
        if info["current_streak"] == 0:
            return False

        # Check if there's a record for today
        row = self.repo.conn.execute(
            "SELECT id FROM streaks WHERE date = ?",
            (today.isoformat(),),
        ).fetchone()

        return row is None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_streak.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add backend/memoryforge/streak/ backend/tests/test_streak.py
git commit -m "feat: streak tracker with at-risk detection"
```

---

## Task 11: Material Processor (Orchestrates Parsing + KU Extraction)

**Files:**
- Create: `backend/memoryforge/parser/material_processor.py`
- Create: `backend/tests/test_material_processor.py` (update existing test_parser.py)

- [ ] **Step 1: Write failing tests**

```python
"""Tests for the material processor (orchestrates parsing + KU extraction)."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from memoryforge.parser.material_processor import MaterialProcessor


class TestMaterialProcessor:
    def test_detect_file_type_pdf(self):
        proc = MaterialProcessor.__new__(MaterialProcessor)
        assert proc._detect_parser("test.pdf") == "pdf"

    def test_detect_file_type_docx(self):
        proc = MaterialProcessor.__new__(MaterialProcessor)
        assert proc._detect_parser("notes.docx") == "docx"

    def test_detect_file_type_txt(self):
        proc = MaterialProcessor.__new__(MaterialProcessor)
        assert proc._detect_parser("notes.txt") == "text"

    def test_detect_file_type_md(self):
        proc = MaterialProcessor.__new__(MaterialProcessor)
        assert proc._detect_parser("notes.md") == "markdown"

    def test_detect_file_type_unknown(self):
        proc = MaterialProcessor.__new__(MaterialProcessor)
        assert proc._detect_parser("image.png") is None

    def test_light_parse_text_file(self, repo, test_config, tmp_path):
        repo.create_subject(name="BIO 301")
        f = tmp_path / "notes.txt"
        f.write_text("Chapter 1\n\nCells are the basic unit of life.")
        mat_id = repo.create_material(
            subject_id=1, filename="notes.txt",
            file_path=str(f), file_type="txt",
            material_type="lecture_notes",
        )
        proc = MaterialProcessor(repo=repo, config=test_config)
        result = proc.light_parse(material_id=mat_id)
        assert result is True
        mat = repo.get_material(mat_id)
        assert mat["parse_status"] == "parsed_light"

    @pytest.mark.asyncio
    async def test_deep_parse_creates_kus(self, repo, test_config, tmp_path):
        repo.create_subject(name="BIO 301")
        f = tmp_path / "notes.txt"
        f.write_text("Mitochondria produce ATP.\n\nDNA stores genetic info.")
        mat_id = repo.create_material(
            subject_id=1, filename="notes.txt",
            file_path=str(f), file_type="txt",
            material_type="lecture_notes",
        )
        proc = MaterialProcessor(repo=repo, config=test_config)
        proc.light_parse(material_id=mat_id)

        mock_response = [
            {
                "concept": "Mitochondria produce ATP through oxidative phosphorylation",
                "concept_summary": "Mitochondria: ATP production",
                "difficulty": 3,
                "tags": ["biology", "cells"],
                "prerequisites": [],
            },
            {
                "concept": "DNA stores genetic information as nucleotide sequences",
                "concept_summary": "DNA: genetic storage",
                "difficulty": 2,
                "tags": ["biology", "genetics"],
                "prerequisites": [],
            },
        ]

        with patch(
            "memoryforge.parser.material_processor.query_claude_json",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            count = await proc.deep_parse(material_id=mat_id)

        assert count == 2
        kus = repo.get_kus_by_subject(1)
        assert len(kus) == 2
        mat = repo.get_material(mat_id)
        assert mat["parse_status"] == "complete"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_material_processor.py -v`
Expected: FAIL

- [ ] **Step 3: Create material_processor.py**

```python
"""Orchestrates document parsing and KU extraction.

Two phases:
1. Light parse — extract text and structure (fast, no Claude)
2. Deep parse — send to Claude for KU extraction (slow, uses tokens)
"""

import json
from pathlib import Path

from memoryforge.config import Config
from memoryforge.db.repository import Repository
from memoryforge.parser.pdf_parser import parse_pdf
from memoryforge.parser.docx_parser import parse_docx
from memoryforge.parser.text_parser import parse_text, parse_markdown
from memoryforge.claude_service.prompts import build_ku_extraction_prompt
from memoryforge.claude_service.client import query_claude_json


class MaterialProcessor:
    """Orchestrates material parsing and KU extraction."""

    def __init__(self, repo: Repository, config: Config) -> None:
        self.repo = repo
        self.config = config

    def _detect_parser(self, filename: str) -> str | None:
        """Detect which parser to use based on file extension."""
        ext = Path(filename).suffix.lower()
        return {
            ".pdf": "pdf",
            ".docx": "docx",
            ".txt": "text",
            ".md": "markdown",
        }.get(ext)

    def light_parse(self, material_id: int) -> bool:
        """Phase 1: Extract text and structure without Claude.

        Returns True if successful.
        """
        mat = self.repo.get_material(material_id)
        if not mat:
            return False

        parser_type = self._detect_parser(mat["filename"])
        if not parser_type:
            self.repo.update_material_status(material_id, "error")
            return False

        file_path = Path(mat["file_path"])
        if not file_path.exists():
            self.repo.update_material_status(material_id, "error")
            return False

        if parser_type == "pdf":
            result = parse_pdf(file_path)
        elif parser_type == "docx":
            result = parse_docx(file_path)
        elif parser_type == "markdown":
            result = parse_markdown(file_path)
        else:
            result = parse_text(file_path)

        outline = json.dumps([s["heading"] for s in result.sections] if result.sections else [])

        self.repo.update_material_status(
            material_id,
            status="parsed_light",
            structure_outline=outline,
        )

        if result.page_count and not mat.get("page_count"):
            self.repo.conn.execute(
                "UPDATE materials SET page_count = ? WHERE id = ?",
                (result.page_count, material_id),
            )
            self.repo.conn.commit()

        return True

    async def deep_parse(self, material_id: int) -> int:
        """Phase 2: Send to Claude for KU extraction.

        Returns the number of KUs created.
        """
        mat = self.repo.get_material(material_id)
        if not mat:
            return 0

        self.repo.update_material_status(material_id, "processing")

        file_path = Path(mat["file_path"])
        parser_type = self._detect_parser(mat["filename"])

        if parser_type == "pdf":
            result = parse_pdf(file_path)
        elif parser_type == "docx":
            result = parse_docx(file_path)
        elif parser_type == "markdown":
            result = parse_markdown(file_path)
        else:
            result = parse_text(file_path)

        subject = self.repo.get_subject(mat["subject_id"])
        subject_name = subject["name"] if subject else "Unknown"

        # Use sections if available, otherwise chunk the full text
        chunks = []
        if result.sections:
            for section in result.sections:
                chunks.append((section.get("heading", ""), section.get("body", "")))
        else:
            # Split into ~1000 char chunks
            text = result.text
            chunk_size = 1000
            for i in range(0, len(text), chunk_size):
                chunks.append((None, text[i:i + chunk_size]))

        total_kus = 0
        for heading, text_chunk in chunks:
            if not text_chunk.strip():
                continue

            prompt = build_ku_extraction_prompt(
                text_chunk=text_chunk,
                subject_name=subject_name,
                section_heading=heading,
            )

            try:
                kus_data = await query_claude_json(prompt)
                if not isinstance(kus_data, list):
                    kus_data = [kus_data]
            except Exception:
                continue

            for ku_data in kus_data:
                self.repo.create_ku(
                    subject_id=mat["subject_id"],
                    material_id=material_id,
                    concept=ku_data.get("concept", ""),
                    concept_summary=ku_data.get("concept_summary", ""),
                    source_location=heading or f"chunk at position {total_kus}",
                    difficulty=ku_data.get("difficulty", 3),
                    tags=json.dumps(ku_data.get("tags", [])),
                    prerequisites=json.dumps(ku_data.get("prerequisites", [])),
                )
                total_kus += 1

        self.repo.update_material_status(material_id, "complete")
        return total_kus
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_material_processor.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/memoryforge/parser/material_processor.py backend/tests/test_material_processor.py
git commit -m "feat: material processor with light parse and Claude-powered KU extraction"
```

---

## Task 12: FastAPI Server

**Files:**
- Create: `backend/memoryforge/api/__init__.py`
- Create: `backend/memoryforge/api/app.py`
- Create: `backend/memoryforge/api/routes_subjects.py`
- Create: `backend/memoryforge/api/routes_materials.py`
- Create: `backend/memoryforge/api/routes_sessions.py`
- Create: `backend/memoryforge/api/routes_dashboard.py`
- Create: `backend/memoryforge/api/routes_plans.py`
- Create: `backend/memoryforge/api/routes_history.py`
- Create: `backend/tests/test_api.py`

- [ ] **Step 1: Write failing API tests**

```python
"""Integration tests for the FastAPI API server."""

from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from memoryforge.api.app import create_app
from memoryforge.config import Config


@pytest.fixture
def app(test_config: Config):
    test_config.ensure_dirs()
    return create_app(config=test_config)


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


class TestSubjectRoutes:
    def test_create_subject(self, client):
        resp = client.post("/api/subjects", json={
            "name": "BIO 301",
            "description": "Molecular Biology",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == 1
        assert data["name"] == "BIO 301"

    def test_list_subjects(self, client):
        client.post("/api/subjects", json={"name": "BIO 301"})
        client.post("/api/subjects", json={"name": "HIST 200"})
        resp = client.get("/api/subjects")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_subject(self, client):
        client.post("/api/subjects", json={"name": "BIO 301"})
        resp = client.get("/api/subjects/1")
        assert resp.status_code == 200
        assert resp.json()["name"] == "BIO 301"

    def test_update_subject(self, client):
        client.post("/api/subjects", json={"name": "BIO 301"})
        resp = client.patch("/api/subjects/1", json={"name": "BIO 302"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "BIO 302"

    def test_get_nonexistent_subject(self, client):
        resp = client.get("/api/subjects/999")
        assert resp.status_code == 404


class TestMaterialRoutes:
    def test_upload_material(self, client, test_config):
        client.post("/api/subjects", json={"name": "BIO 301"})
        test_config.ensure_dirs()
        test_file = test_config.uploads_dir / "test.txt"
        test_file.write_text("Cell biology content.")

        with open(str(test_file), "rb") as f:
            resp = client.post(
                "/api/materials/upload",
                data={"subject_id": "1", "material_type": "lecture_notes"},
                files={"file": ("test.txt", f, "text/plain")},
            )
        assert resp.status_code == 201
        assert resp.json()["filename"] == "test.txt"

    def test_list_materials(self, client, test_config):
        client.post("/api/subjects", json={"name": "BIO 301"})
        test_config.ensure_dirs()
        test_file = test_config.uploads_dir / "test.txt"
        test_file.write_text("Content")

        with open(str(test_file), "rb") as f:
            client.post(
                "/api/materials/upload",
                data={"subject_id": "1", "material_type": "textbook"},
                files={"file": ("test.txt", f, "text/plain")},
            )
        resp = client.get("/api/materials?subject_id=1")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestSessionRoutes:
    def test_start_session(self, client):
        resp = client.post("/api/sessions/start")
        assert resp.status_code == 201
        assert "session_id" in resp.json()

    def test_end_session(self, client):
        start = client.post("/api/sessions/start")
        session_id = start.json()["session_id"]
        resp = client.post(f"/api/sessions/{session_id}/end")
        assert resp.status_code == 200
        assert "correct" in resp.json()


class TestDashboardRoutes:
    def test_dashboard_empty(self, client):
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "due_count" in data
        assert "streak" in data
        assert data["due_count"] == 0

    def test_dashboard_with_data(self, client):
        client.post("/api/subjects", json={"name": "BIO 301"})
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        assert "subjects_summary" in resp.json()


class TestHistoryRoutes:
    def test_performance_empty(self, client):
        resp = client.get("/api/history/performance")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_reviews" in data
        assert data["total_reviews"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_api.py -v`
Expected: FAIL

- [ ] **Step 3: Create api/__init__.py**

```python
"""FastAPI application for MemoryForge."""
```

- [ ] **Step 4: Create app.py**

```python
"""FastAPI app factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from memoryforge.config import Config, get_config
from memoryforge.db.connection import get_connection
from memoryforge.db.repository import Repository
from memoryforge.api.routes_subjects import router as subjects_router
from memoryforge.api.routes_materials import router as materials_router
from memoryforge.api.routes_sessions import router as sessions_router
from memoryforge.api.routes_dashboard import router as dashboard_router
from memoryforge.api.routes_plans import router as plans_router
from memoryforge.api.routes_history import router as history_router


def create_app(config: Config | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if config is None:
        config = get_config()

    config.ensure_dirs()

    app = FastAPI(
        title="MemoryForge",
        version="0.1.0",
        description="AI-powered adaptive learning API",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Shared state
    conn = get_connection(config.db_path)
    repo = Repository(conn)

    app.state.config = config
    app.state.repo = repo

    # Register routes
    app.include_router(subjects_router, prefix="/api")
    app.include_router(materials_router, prefix="/api")
    app.include_router(sessions_router, prefix="/api")
    app.include_router(dashboard_router, prefix="/api")
    app.include_router(plans_router, prefix="/api")
    app.include_router(history_router, prefix="/api")

    return app
```

- [ ] **Step 5: Create routes_subjects.py**

```python
"""Subject CRUD endpoints."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(tags=["subjects"])


class CreateSubjectRequest(BaseModel):
    name: str
    description: str = ""
    interleave_ratio: float = 0.3
    grading_strictness: int = 2
    quiz_format: str = "mixed"


class UpdateSubjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    interleave_ratio: float | None = None
    grading_strictness: int | None = None
    quiz_format: str | None = None


@router.post("/subjects", status_code=201)
def create_subject(body: CreateSubjectRequest, request: Request):
    repo = request.app.state.repo
    subject_id = repo.create_subject(
        name=body.name,
        description=body.description,
        interleave_ratio=body.interleave_ratio,
        grading_strictness=body.grading_strictness,
        quiz_format=body.quiz_format,
    )
    return repo.get_subject(subject_id)


@router.get("/subjects")
def list_subjects(request: Request, active_only: bool = False):
    return request.app.state.repo.list_subjects(active_only=active_only)


@router.get("/subjects/{subject_id}")
def get_subject(subject_id: int, request: Request):
    subject = request.app.state.repo.get_subject(subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


@router.patch("/subjects/{subject_id}")
def update_subject(subject_id: int, body: UpdateSubjectRequest, request: Request):
    repo = request.app.state.repo
    subject = repo.get_subject(subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    updates = body.model_dump(exclude_none=True)
    if updates:
        repo.update_subject(subject_id, **updates)
    return repo.get_subject(subject_id)
```

- [ ] **Step 6: Create routes_materials.py**

```python
"""Material upload and management endpoints."""

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form

from memoryforge.parser.material_processor import MaterialProcessor

router = APIRouter(tags=["materials"])

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}
MAX_FILENAME_LENGTH = 255


@router.post("/materials/upload", status_code=201)
async def upload_material(
    request: Request,
    subject_id: int = Form(...),
    material_type: str = Form("textbook"),
    file: UploadFile = File(...),
):
    repo = request.app.state.repo
    config = request.app.state.config

    subject = repo.get_subject(subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}",
        )

    safe_name = f"{uuid4().hex}{ext}"
    dest = config.uploads_dir / safe_name

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_type = ext.lstrip(".")
    mat_id = repo.create_material(
        subject_id=subject_id,
        filename=file.filename[:MAX_FILENAME_LENGTH],
        file_path=str(dest),
        file_type=file_type,
        material_type=material_type,
    )

    processor = MaterialProcessor(repo=repo, config=config)
    processor.light_parse(material_id=mat_id)

    return repo.get_material(mat_id)


@router.get("/materials")
def list_materials(request: Request, subject_id: int | None = None):
    return request.app.state.repo.list_materials(subject_id=subject_id)


@router.get("/materials/{material_id}")
def get_material(material_id: int, request: Request):
    mat = request.app.state.repo.get_material(material_id)
    if not mat:
        raise HTTPException(status_code=404, detail="Material not found")
    return mat


@router.post("/materials/{material_id}/parse-now")
async def parse_now(material_id: int, request: Request):
    repo = request.app.state.repo
    config = request.app.state.config

    mat = repo.get_material(material_id)
    if not mat:
        raise HTTPException(status_code=404, detail="Material not found")

    if mat.get("page_count") and mat["page_count"] > config.parse_now_max_pages:
        raise HTTPException(
            status_code=400,
            detail=f"File has {mat['page_count']} pages (max {config.parse_now_max_pages} for immediate parsing). Queued for nightly batch.",
        )

    processor = MaterialProcessor(repo=repo, config=config)
    count = await processor.deep_parse(material_id=material_id)
    return {"knowledge_units_created": count}
```

- [ ] **Step 7: Create routes_sessions.py**

```python
"""Study session endpoints."""

from datetime import date

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from memoryforge.session.engine import SessionEngine
from memoryforge.scheduler.context_aware import build_session_queue

router = APIRouter(tags=["sessions"])


class RecordTurnRequest(BaseModel):
    ku_id: int | None = None
    turn_type: str
    question_text: str
    student_response: str | None = None
    claude_feedback: str | None = None
    grade: int | None = None
    time_taken_seconds: int | None = None


# Store active session engines in memory (single-user app)
_active_engines: dict[int, SessionEngine] = {}


@router.post("/sessions/start", status_code=201)
def start_session(request: Request):
    repo = request.app.state.repo
    engine = SessionEngine(repo=repo)
    session_id = engine.start_session()

    due_kus = repo.get_due_kus(today=date.today())
    queue = build_session_queue(
        due_kus=due_kus,
        new_topics=[],
        interleave_ratio=0.3,
    )
    engine.set_queue(queue)

    _active_engines[session_id] = engine

    return {
        "session_id": session_id,
        "queue_length": len(queue),
    }


@router.get("/sessions/{session_id}/next")
def get_next_item(session_id: int):
    engine = _active_engines.get(session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Session not found or not active")

    item = engine.get_next_item()
    if item is None:
        return {"done": True}

    return {
        "done": False,
        "activity_type": item.activity_type,
        "ku": item.ku,
        "topic_info": item.topic_info,
    }


@router.post("/sessions/{session_id}/turn")
def record_turn(session_id: int, body: RecordTurnRequest, request: Request):
    engine = _active_engines.get(session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Session not found or not active")

    turn_id = engine.record_turn(
        ku_id=body.ku_id,
        turn_type=body.turn_type,
        question_text=body.question_text,
        student_response=body.student_response,
        claude_feedback=body.claude_feedback,
        grade=body.grade,
        time_taken_seconds=body.time_taken_seconds,
    )

    return {
        "turn_id": turn_id,
        "needs_reteach": list(engine.needs_reteach),
    }


@router.post("/sessions/{session_id}/end")
def end_session(session_id: int):
    engine = _active_engines.get(session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Session not found or not active")

    summary = engine.end_session()
    del _active_engines[session_id]
    return summary


@router.get("/sessions/{session_id}")
def get_session(session_id: int, request: Request):
    session = request.app.state.repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
```

- [ ] **Step 8: Create routes_dashboard.py**

```python
"""Dashboard data endpoints."""

from datetime import date

from fastapi import APIRouter, Request

from memoryforge.streak.tracker import StreakTracker

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(request: Request):
    repo = request.app.state.repo
    tracker = StreakTracker(repo=repo)

    due_kus = repo.get_due_kus(today=date.today())
    subjects = repo.list_subjects(active_only=True)

    subjects_summary = []
    for subject in subjects:
        kus = repo.get_kus_by_subject(subject["id"])
        total = len(kus)
        mastered = sum(1 for ku in kus if ku.get("repetitions", 0) >= 3)
        subjects_summary.append({
            "id": subject["id"],
            "name": subject["name"],
            "total_kus": total,
            "mastered_kus": mastered,
            "mastery_pct": round(mastered / total * 100, 1) if total > 0 else 0,
        })

    streak_info = tracker.get_info()

    return {
        "due_count": len(due_kus),
        "streak": streak_info,
        "streak_at_risk": tracker.is_at_risk(today=date.today()),
        "subjects_summary": subjects_summary,
    }
```

- [ ] **Step 9: Create routes_plans.py**

```python
"""Learning plan endpoints."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(tags=["plans"])


class CreatePlanRequest(BaseModel):
    subject_id: int
    plan_data: str = "{}"
    deadlines: str = "{}"
    focus_areas: str = "[]"


@router.post("/plans", status_code=201)
def create_plan(body: CreatePlanRequest, request: Request):
    repo = request.app.state.repo
    plan_id = repo.create_learning_plan(
        subject_id=body.subject_id,
        plan_data=body.plan_data,
        deadlines=body.deadlines,
        focus_areas=body.focus_areas,
    )
    return repo.get_learning_plan(subject_id=body.subject_id)


@router.get("/plans/{subject_id}")
def get_plan(subject_id: int, request: Request):
    plan = request.app.state.repo.get_learning_plan(subject_id=subject_id)
    if not plan:
        raise HTTPException(status_code=404, detail="No plan found for this subject")
    return plan
```

- [ ] **Step 10: Create routes_history.py**

```python
"""Performance history endpoints."""

from fastapi import APIRouter, Request

router = APIRouter(tags=["history"])


@router.get("/history/performance")
def get_performance(request: Request, subject_id: int | None = None):
    repo = request.app.state.repo

    rows = repo.conn.execute(
        "SELECT COUNT(*) as total FROM review_history"
    ).fetchone()
    total_reviews = rows["total"] if rows else 0

    if total_reviews == 0:
        return {
            "total_reviews": 0,
            "average_quality": 0,
            "by_subject": [],
        }

    avg = repo.conn.execute(
        "SELECT AVG(quality) as avg_q FROM review_history"
    ).fetchone()

    by_subject = []
    subjects = repo.list_subjects()
    for subject in subjects:
        sub_reviews = repo.conn.execute(
            """SELECT COUNT(*) as cnt, AVG(rh.quality) as avg_q
               FROM review_history rh
               JOIN knowledge_units ku ON rh.ku_id = ku.id
               WHERE ku.subject_id = ?""",
            (subject["id"],),
        ).fetchone()
        if sub_reviews and sub_reviews["cnt"] > 0:
            by_subject.append({
                "subject_id": subject["id"],
                "subject_name": subject["name"],
                "review_count": sub_reviews["cnt"],
                "average_quality": round(sub_reviews["avg_q"], 2),
            })

    return {
        "total_reviews": total_reviews,
        "average_quality": round(avg["avg_q"], 2) if avg and avg["avg_q"] else 0,
        "by_subject": by_subject,
    }


@router.get("/history/ku/{ku_id}")
def get_ku_history(ku_id: int, request: Request):
    repo = request.app.state.repo
    reviews = repo.get_review_history(ku_id=ku_id)
    ku = repo.get_ku(ku_id)
    return {
        "ku": ku,
        "reviews": reviews,
        "total_reviews": len(reviews),
    }
```

- [ ] **Step 11: Run tests to verify they pass**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/test_api.py -v`
Expected: All PASS

- [ ] **Step 12: Commit**

```bash
git add backend/memoryforge/api/ backend/tests/test_api.py
git commit -m "feat: FastAPI server with all REST endpoints for subjects, materials, sessions, dashboard, plans, and history"
```

---

## Task 13: Run Full Test Suite + Final Verification

**Files:** No new files

- [ ] **Step 1: Run complete test suite**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Verify API server starts**

Run: `cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && python -c "from memoryforge.api.app import create_app; app = create_app(); print('App created successfully')"`
Expected: `App created successfully`

- [ ] **Step 3: Final commit with all files**

```bash
git add -A
git commit -m "feat: complete MemoryForge backend — core library + API server

Includes: SM-2 engine, database layer, Claude service with 3-layer
token efficiency, material parsers, context-aware scheduler, session
engine, streak tracker, question type registry, and FastAPI REST API."
```

- [ ] **Step 4: Push to remote**

```bash
git push origin main
```

---

## What This Plan Produces

After completing all 13 tasks, you will have:

- A fully tested Python backend with 80+ test cases
- SM-2 spaced repetition (pure math, no Claude)
- Context-aware scheduler with interleaving and prerequisites
- Material parsing for PDF, DOCX, text, markdown
- Claude integration with prompt templates and 3-layer token efficiency
- Pluggable question type registry
- Study session engine with re-teach tracking
- Streak system
- REST API covering all 6 screen data needs
- Everything testable without the Electron frontend

## Next Plans

- **Plan 2: Electron + React Frontend** — 6 screens consuming this API
- **Plan 3: Nightly Daemon + v2 Features** — launchd service, syllabus parsing, corpora, pre-generation
