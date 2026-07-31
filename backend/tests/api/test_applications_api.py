import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db import session as db_session
from app.db.models import Job, Application


@pytest.fixture
def client():
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
            source_url="https://example.com/job/1",
            source_site="manual",
            dedupe_key="acme|genai architect|chennai",
            tailored_resume="SUMMARY\n...",
            tailored_cover_letter="Dear Hiring Manager,\n...",
            status="approved",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        session.add(Application(job_id=job.id, status="approved"))
        session.commit()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_applications_includes_job_details(client):
    response = client.get("/applications")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["job_title"] == "GenAI Architect"
    assert body[0]["job_company"] == "Acme"
    assert body[0]["has_tailored_resume"] is True
    assert body[0]["has_tailored_cover_letter"] is True
