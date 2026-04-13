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
