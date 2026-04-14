"""Dashboard summary route."""

from datetime import date

from fastapi import APIRouter, Request

from memoryforge.streak.tracker import StreakTracker

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(request: Request):
    repo = request.app.state.repo
    today = date.today()

    due_kus = repo.get_due_kus(today)
    due_count = len(due_kus)

    streak_tracker = StreakTracker(repo)
    streak_info = streak_tracker.get_info()
    streak_at_risk = streak_tracker.is_at_risk(today)

    subjects = repo.list_subjects(active_only=True)
    subjects_summary = []
    for subject in subjects:
        kus = repo.get_kus_by_subject(subject["id"])
        total = len(kus)
        mastered = sum(1 for ku in kus if ku.get("easiness_factor", 2.5) >= 2.5 and ku.get("interval", 0) >= 7)
        subjects_summary.append({
            "id": subject["id"],
            "name": subject["name"],
            "total_kus": total,
            "mastered_kus": mastered,
            "mastery_pct": round(mastered / total * 100, 1) if total else 0.0,
        })

    return {
        "due_count": due_count,
        "streak": streak_info,
        "streak_at_risk": streak_at_risk,
        "subjects_summary": subjects_summary,
    }
