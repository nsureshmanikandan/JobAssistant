import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db import session as db_session
from app.db.models import ResumeVersion
from app.services.scoring import ScoreResult


@pytest.fixture
def client_with_master_resume():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[db_session.get_session] = override_get_session
    with Session(engine) as session:
        session.add(ResumeVersion(label="master", content="master resume text", is_master=True))
        session.commit()
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def fake_score_job(llm, resume, job_description, criteria):
    return ScoreResult(
        match_percentage=88,
        matched_skills=["Python"],
        missing_skills=[],
        sponsorship_required=False,
        company_size_estimate="10000+",
        reasoning="Good match.",
    )


def test_manual_job_with_description_gets_scored(client_with_master_resume, monkeypatch):
    monkeypatch.setattr("app.api.jobs.score_job", fake_score_job)

    response = client_with_master_resume.post(
        "/jobs/manual",
        json={
            "title": "GenAI Architect",
            "company": "Acme",
            "location": "Chennai",
            "source_url": "https://example.com/job",
            "description": "We need a GenAI Architect.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["match_percentage"] == 88
    assert body["sponsorship_required"] is False

    # Scoring calls must show up in the Observability log, same as tailoring calls.
    llm_calls = client_with_master_resume.get("/observability/llm-calls").json()
    assert len(llm_calls) == 1
    assert llm_calls[0]["prompt_id"] == "scoring-v1"
    assert llm_calls[0]["success"] is True


def test_manual_job_without_description_stays_unscored(client_with_master_resume):
    response = client_with_master_resume.post(
        "/jobs/manual",
        json={
            "title": "GenAI Architect",
            "company": "Acme",
            "location": "Chennai",
            "source_url": "https://example.com/job",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["match_percentage"] is None
    assert body["needs_manual_paste"] is True
