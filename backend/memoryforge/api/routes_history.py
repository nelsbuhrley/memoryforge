"""Performance history routes."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/performance")
def get_performance(request: Request, subject_id: int | None = None, limit: int = 100):
    repo = request.app.state.repo

    query = """
        SELECT
            st.id,
            st.session_id,
            st.ku_id,
            ku.concept AS ku_title,
            ku.subject_id,
            st.grade,
            CASE WHEN st.grade IS NOT NULL AND st.grade >= 3 THEN 1 ELSE 0 END AS correct,
            st.created_at AS reviewed_at
        FROM session_turns st
        JOIN knowledge_units ku ON ku.id = st.ku_id
    """
    params: list = []
    if subject_id is not None:
        query += " WHERE ku.subject_id = ?"
        params.append(subject_id)
    query += " ORDER BY st.created_at DESC LIMIT ?"
    params.append(limit)

    rows = repo.conn.execute(query, params).fetchall()
    keys = ["id", "session_id", "ku_id", "ku_title", "subject_id", "grade", "correct", "reviewed_at"]
    return [dict(zip(keys, row)) for row in rows]
