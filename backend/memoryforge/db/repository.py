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
