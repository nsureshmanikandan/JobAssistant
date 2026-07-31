import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db import session as db_session
from app.db.models import Job


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[db_session.get_session] = override_get_session
    with Session(engine) as session:
        job = Job(
            title="GenAI Architect",
            company="Acme",
            location="Chennai",
            source_url="https://example.com/1",
            source_site="linkedin",
            dedupe_key="acme|genai architect|chennai",
            match_percentage=90,
            sponsorship_required=False,
            status="pending_review",
        )
        session.add(job)
        session.commit()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_jobs_returns_pending_job(client):
    response = client.get("/jobs")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "GenAI Architect"


def test_reject_job_updates_status(client):
    list_response = client.get("/jobs")
    job_id = list_response.json()[0]["id"]
    response = client.post(f"/jobs/{job_id}/reject")
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
