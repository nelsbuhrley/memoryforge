"""FastAPI integration tests."""

import io
import pytest
from fastapi.testclient import TestClient

from memoryforge.api.app import create_app
from memoryforge.config import Config


@pytest.fixture
def client(test_config: Config) -> TestClient:
    app = create_app(config=test_config)
    return TestClient(app)


@pytest.fixture
def subject_id(client: TestClient) -> int:
    res = client.post("/subjects", json={"name": "Physics", "description": "Classical mechanics"})
    assert res.status_code == 201
    return res.json()["id"]


# --- Subject routes ---

class TestSubjectRoutes:
    def test_list_subjects_empty(self, client: TestClient):
        res = client.get("/subjects")
        assert res.status_code == 200
        assert res.json() == []

    def test_create_subject(self, client: TestClient):
        res = client.post("/subjects", json={"name": "Math"})
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Math"
        assert "id" in data

    def test_get_subject(self, client: TestClient, subject_id: int):
        res = client.get(f"/subjects/{subject_id}")
        assert res.status_code == 200
        assert res.json()["id"] == subject_id

    def test_get_subject_not_found(self, client: TestClient):
        res = client.get("/subjects/9999")
        assert res.status_code == 404

    def test_update_subject(self, client: TestClient, subject_id: int):
        res = client.patch(f"/subjects/{subject_id}", json={"name": "Updated Physics"})
        assert res.status_code == 200
        assert res.json()["name"] == "Updated Physics"


# --- Material routes ---

class TestMaterialRoutes:
    def test_list_materials_empty(self, client: TestClient):
        res = client.get("/materials")
        assert res.status_code == 200
        assert res.json() == []

    def test_upload_material(self, client: TestClient, subject_id: int, test_config: Config):
        test_config.uploads_dir.mkdir(parents=True, exist_ok=True)
        file_content = b"Chapter 1: Motion\nVelocity is the rate of change of position."
        res = client.post(
            "/materials",
            data={"subject_id": subject_id},
            files={"file": ("test_chapter.txt", io.BytesIO(file_content), "text/plain")},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["subject_id"] == subject_id
        assert "id" in data


# --- Session routes ---

class TestSessionRoutes:
    def test_start_session_no_due_kus(self, client: TestClient, subject_id: int):
        res = client.post("/sessions/start", json={"subject_id": subject_id})
        assert res.status_code == 422

    def test_end_session_not_found(self, client: TestClient):
        res = client.post("/sessions/9999/end")
        assert res.status_code == 404


# --- Dashboard routes ---

class TestDashboardRoutes:
    def test_dashboard_empty(self, client: TestClient):
        res = client.get("/dashboard")
        assert res.status_code == 200
        data = res.json()
        assert "due_count" in data
        assert "streak" in data
        assert "streak_at_risk" in data
        assert "subjects_summary" in data

    def test_dashboard_due_count_zero(self, client: TestClient):
        res = client.get("/dashboard")
        assert res.json()["due_count"] == 0


# --- History routes ---

class TestHistoryRoutes:
    def test_performance_empty(self, client: TestClient):
        res = client.get("/history/performance")
        assert res.status_code == 200
        assert res.json() == []
