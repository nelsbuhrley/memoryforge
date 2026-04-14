"""Learning plan routes."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/plans", tags=["plans"])


class PlanCreate(BaseModel):
    subject_id: int
    plan_data: str
    deadlines: str = ""
    focus_areas: str = ""


@router.get("/{subject_id}")
def get_plan(subject_id: int, request: Request):
    repo = request.app.state.repo
    plan = repo.get_learning_plan(subject_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="No plan for this subject")
    return plan


@router.post("", status_code=201)
def create_plan(body: PlanCreate, request: Request):
    repo = request.app.state.repo
    repo.create_learning_plan(
        subject_id=body.subject_id,
        plan_data=body.plan_data,
        deadlines=body.deadlines,
        focus_areas=body.focus_areas,
    )
    return repo.get_learning_plan(body.subject_id)
