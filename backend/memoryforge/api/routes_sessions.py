"""Session lifecycle routes."""

from datetime import date

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from memoryforge.scheduler.context_aware import build_session_queue
from memoryforge.session.engine import SessionEngine, SessionState
from memoryforge.session.question_registry import QuestionRegistry

router = APIRouter(prefix="/sessions", tags=["sessions"])

# In-memory store: session_id -> SessionEngine
_active_engines: dict[int, SessionEngine] = {}


class StartSession(BaseModel):
    subject_id: int | None = None
    quiz_format: str = "free_response"


class TurnBody(BaseModel):
    answer: str


@router.post("/start", status_code=201)
def start_session(body: StartSession, request: Request):
    repo = request.app.state.repo
    today = date.today()

    due_kus = repo.get_due_kus(today, subject_id=body.subject_id)
    queue = build_session_queue(due_kus, [])

    if not queue:
        raise HTTPException(status_code=422, detail="No due knowledge units")

    session_id = repo.create_session()
    first_item = queue[0]

    engine = SessionEngine(
        ku=first_item.ku,
        quiz_format=body.quiz_format,
    )
    _active_engines[session_id] = engine

    registry = QuestionRegistry()
    question = registry.generate(first_item.ku, body.quiz_format)

    return {
        "session_id": session_id,
        "queue_length": len(queue),
        "current_ku": first_item.ku,
        "question": question,
    }


@router.get("/{session_id}/next")
def next_question(session_id: int, request: Request):
    if session_id not in _active_engines:
        raise HTTPException(status_code=404, detail="Session not found")

    engine = _active_engines[session_id]
    repo = request.app.state.repo
    session = repo.get_session(session_id)

    return {
        "session_id": session_id,
        "state": engine.state.value,
        "ku": engine.ku,
    }


@router.post("/{session_id}/turn")
async def session_turn(session_id: int, body: TurnBody, request: Request):
    if session_id not in _active_engines:
        raise HTTPException(status_code=404, detail="Session not found")

    engine = _active_engines[session_id]
    grade_result = await engine.grade_answer(body.answer)

    repo = request.app.state.repo
    repo.create_session_turn(
        session_id=session_id,
        ku_id=engine.ku["id"],
        turn_type="quiz",
        question_text="",
        student_response=body.answer,
        claude_feedback=grade_result.feedback,
        grade=grade_result.grade,
        time_taken_seconds=None,
    )

    reteach = None
    if not grade_result.correct:
        reteach = await engine.reteach_answer()

    return {
        "correct": grade_result.correct,
        "grade": grade_result.grade,
        "feedback": grade_result.feedback,
        "reteach": reteach,
    }


@router.post("/{session_id}/end")
def end_session(session_id: int, request: Request):
    if session_id not in _active_engines:
        raise HTTPException(status_code=404, detail="Session not found")

    engine = _active_engines.pop(session_id)
    engine.complete_session()

    repo = request.app.state.repo
    turns = repo.get_session_turns(session_id)
    correct = sum(1 for t in turns if t.get("correct"))
    total = len(turns)

    repo.end_session(session_id, subjects_covered="", score_summary=f"{correct}/{total}")

    return {
        "session_id": session_id,
        "correct": correct,
        "total": total,
        "accuracy": correct / total if total else 0.0,
    }
