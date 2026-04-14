"""Subject CRUD routes."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/subjects", tags=["subjects"])


class SubjectCreate(BaseModel):
    name: str
    description: str = ""
    quiz_format: str = "mixed"
    grading_strictness: int = 2


class SubjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    active: bool | None = None


@router.get("")
def list_subjects(request: Request, active_only: bool = False):
    repo = request.app.state.repo
    return repo.list_subjects(active_only=active_only)


@router.post("", status_code=201)
def create_subject(body: SubjectCreate, request: Request):
    repo = request.app.state.repo
    subject_id = repo.create_subject(
        name=body.name,
        description=body.description,
        quiz_format=body.quiz_format,
        grading_strictness=body.grading_strictness,
    )
    return repo.get_subject(subject_id)


@router.get("/{subject_id}")
def get_subject(subject_id: int, request: Request):
    repo = request.app.state.repo
    subject = repo.get_subject(subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


@router.patch("/{subject_id}")
def update_subject(subject_id: int, body: SubjectUpdate, request: Request):
    repo = request.app.state.repo
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    repo.update_subject(subject_id, **updates)
    return repo.get_subject(subject_id)
