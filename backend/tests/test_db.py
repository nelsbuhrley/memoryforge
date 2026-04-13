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
