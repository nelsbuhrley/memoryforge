"""Admin routes — force-trigger nightly batch jobs individually or all at once."""

import json
from datetime import date, datetime

from fastapi import APIRouter, Request, Query

from memoryforge.parser.material_processor import MaterialProcessor
from memoryforge.claude_service.prompts import build_learning_plan_prompt
from memoryforge.claude_service.client import query_claude_json

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ku_count_for(repo, material_id: int) -> int:
    row = repo.conn.execute(
        "SELECT COUNT(*) FROM knowledge_units WHERE material_id = ?", (material_id,)
    ).fetchone()
    return row[0] if row else 0


async def _run_parse_job(repo, config, force: bool = False) -> dict:
    """Job 1: Deep parse pending (or all zero-KU complete) materials."""
    materials = repo.list_materials()
    if force:
        pending = [
            m for m in materials
            if m.get("parse_status") in ("uploaded", "parsed_light")
            or (m.get("parse_status") == "complete" and _ku_count_for(repo, m["id"]) == 0)
        ]
    else:
        pending = [m for m in materials if m.get("parse_status") in ("uploaded", "parsed_light")]

    processor = MaterialProcessor(repo=repo, config=config)
    parsed_counts, parse_errors = [], []
    for mat in pending:
        try:
            ku_count = await processor.deep_parse(mat["id"])
            parsed_counts.append({"material_id": mat["id"], "filename": mat["filename"], "ku_count": ku_count})
        except Exception as exc:
            parse_errors.append({"material_id": mat["id"], "filename": mat["filename"], "error": str(exc)})

    return {
        "processed": len(parsed_counts),
        "errors": len(parse_errors),
        "details": parsed_counts,
        "error_details": parse_errors,
    }


async def _run_plans_job(repo) -> dict:
    """Job 2: Regenerate learning plans for all active subjects."""
    subjects = repo.list_subjects(active_only=True)
    plan_updates, plan_errors = [], []
    for subject in subjects:
        try:
            kus = repo.get_kus_by_subject(subject["id"])
            if not kus:
                continue
            material_outline = ", ".join(
                ku.get("concept_summary", "") for ku in kus[:30] if ku.get("concept_summary")
            )
            mastered = sum(1 for ku in kus if (ku.get("repetitions") or 0) >= 3)
            prompt = build_learning_plan_prompt(
                subject_name=subject["name"],
                material_outline=material_outline or "General material",
                current_progress=f"{mastered}/{len(kus)} KUs mastered",
                deadlines="None specified",
            )
            plan_data = await query_claude_json(prompt)
            repo.create_learning_plan(
                subject_id=subject["id"],
                plan_data=json.dumps(plan_data),
                deadlines="",
                focus_areas=json.dumps(plan_data.get("focus_areas", [])),
            )
            plan_updates.append({"subject_id": subject["id"], "name": subject["name"]})
        except Exception as exc:
            plan_errors.append({"subject_id": subject["id"], "name": subject["name"], "error": str(exc)})
    return {"updated": len(plan_updates), "errors": len(plan_errors), "details": plan_updates}


def _run_decay_job(repo) -> dict:
    """Job 3: Flag KUs overdue by >7 days."""
    today = date.today()
    subjects = repo.list_subjects(active_only=True)
    all_kus = []
    for subject in subjects:
        all_kus.extend(repo.get_kus_by_subject(subject["id"]))

    overdue = []
    for ku in all_kus:
        nr = ku.get("next_review")
        if nr and nr < today.isoformat():
            days_overdue = (today - datetime.fromisoformat(nr).date()).days
            if days_overdue > 7:
                overdue.append({
                    "ku_id": ku["id"],
                    "concept_summary": ku.get("concept_summary", ""),
                    "days_overdue": days_overdue,
                })
    return {"overdue_kus": len(overdue), "details": overdue[:20]}


def _run_analytics_job(repo) -> dict:
    """Job 4: Analytics rollup."""
    today = date.today()
    subjects = repo.list_subjects(active_only=True)
    all_kus = []
    for subject in subjects:
        all_kus.extend(repo.get_kus_by_subject(subject["id"]))
    return {
        "due_today": len(repo.get_due_kus(today)),
        "total_kus": len(all_kus),
        "total_subjects": len(subjects),
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/nightly")
async def run_nightly(request: Request, force: bool = Query(False)):
    """Run all 4 nightly batch jobs.

    ?force=true also re-parses complete materials that have 0 KUs.
    """
    repo = request.app.state.repo
    config = request.app.state.config
    return {
        "status": "complete",
        "ran_at": date.today().isoformat(),
        "results": {
            "job1_parse_materials": await _run_parse_job(repo, config, force=force),
            "job2_update_plans": await _run_plans_job(repo),
            "job3_decay_detection": _run_decay_job(repo),
            "job4_analytics": _run_analytics_job(repo),
        },
    }


@router.post("/parse-materials")
async def parse_materials(request: Request, force: bool = Query(False)):
    """Job 1 only: deep parse pending materials.

    ?force=true also re-parses complete materials with 0 KUs.
    """
    repo = request.app.state.repo
    config = request.app.state.config
    result = await _run_parse_job(repo, config, force=force)
    return {"status": "complete", "ran_at": date.today().isoformat(), **result}


@router.post("/update-plans")
async def update_plans(request: Request):
    """Job 2 only: regenerate learning plans for all active subjects."""
    result = await _run_plans_job(request.app.state.repo)
    return {"status": "complete", "ran_at": date.today().isoformat(), **result}


@router.post("/decay-detection")
def decay_detection(request: Request):
    """Job 3 only: flag KUs overdue by >7 days."""
    result = _run_decay_job(request.app.state.repo)
    return {"status": "complete", "ran_at": date.today().isoformat(), **result}


@router.post("/analytics")
def analytics_rollup(request: Request):
    """Job 4 only: analytics rollup."""
    result = _run_analytics_job(request.app.state.repo)
    return {"status": "complete", "ran_at": date.today().isoformat(), **result}
