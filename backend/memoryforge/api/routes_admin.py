"""Admin routes — force-trigger nightly batch jobs."""

import json
from datetime import date

from fastapi import APIRouter, Request

from memoryforge.parser.material_processor import MaterialProcessor
from memoryforge.claude_service.prompts import build_learning_plan_prompt
from memoryforge.claude_service.client import query_claude_json

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/nightly")
async def run_nightly(request: Request):
    """Run all nightly batch jobs immediately.

    Jobs (in order):
    1. Deep parse pending materials
    2. Update learning plans per active subject
    3. Decay detection — flag KUs overdue by >7 days
    4. Analytics rollup — aggregate session performance
    """
    repo = request.app.state.repo
    config = request.app.state.config
    results = {}

    # ── Job 1: Deep parse pending materials ──────────────────────────────────
    materials = repo.list_materials()
    pending = [m for m in materials if m.get("parse_status") in ("uploaded", "parsed_light")]
    processor = MaterialProcessor(repo=repo, config=config)

    parsed_counts = []
    parse_errors = []
    for mat in pending:
        try:
            ku_count = await processor.deep_parse(mat["id"])
            parsed_counts.append({"material_id": mat["id"], "filename": mat["filename"], "ku_count": ku_count})
        except Exception as exc:
            parse_errors.append({"material_id": mat["id"], "filename": mat["filename"], "error": str(exc)})

    results["job1_parse_materials"] = {
        "processed": len(parsed_counts),
        "errors": len(parse_errors),
        "details": parsed_counts,
        "error_details": parse_errors,
    }

    # ── Job 2: Update learning plans for active subjects ─────────────────────
    subjects = repo.list_subjects(active_only=True)
    plan_updates = []
    plan_errors = []

    for subject in subjects:
        try:
            kus = repo.get_kus_by_subject(subject["id"])
            if not kus:
                continue

            # Build material outline from KU tags/summaries
            material_outline = ", ".join(
                ku.get("concept_summary", "") for ku in kus[:30] if ku.get("concept_summary")
            )

            # Summarize current progress (mastered = repetitions >= 3)
            mastered = sum(1 for ku in kus if (ku.get("repetitions") or 0) >= 3)
            progress = f"{mastered}/{len(kus)} KUs mastered"

            prompt = build_learning_plan_prompt(
                subject_name=subject["name"],
                material_outline=material_outline or "General material",
                current_progress=progress,
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

    results["job2_update_plans"] = {
        "updated": len(plan_updates),
        "errors": len(plan_errors),
        "details": plan_updates,
    }

    # ── Job 3: Decay detection ────────────────────────────────────────────────
    today = date.today()
    all_kus = []
    for subject in subjects:
        all_kus.extend(repo.get_kus_by_subject(subject["id"]))

    overdue = []
    for ku in all_kus:
        next_review = ku.get("next_review")
        if next_review and next_review < today.isoformat():
            from datetime import datetime
            review_date = datetime.fromisoformat(next_review).date()
            days_overdue = (today - review_date).days
            if days_overdue > 7:
                overdue.append({
                    "ku_id": ku["id"],
                    "concept_summary": ku.get("concept_summary", ""),
                    "days_overdue": days_overdue,
                })

    results["job3_decay_detection"] = {
        "overdue_kus": len(overdue),
        "details": overdue[:20],  # cap at 20 to keep response small
    }

    # ── Job 4: Analytics rollup ───────────────────────────────────────────────
    total_due = len(repo.get_due_kus(today))
    results["job4_analytics"] = {
        "due_today": total_due,
        "total_kus": len(all_kus),
        "total_subjects": len(subjects),
    }

    return {
        "status": "complete",
        "ran_at": today.isoformat(),
        "results": results,
    }
