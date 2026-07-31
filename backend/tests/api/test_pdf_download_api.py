import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db import session as db_session
from app.db.models import Job, ResumeVersion


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
        session.add(ResumeVersion(label="master", content="Jane Doe\n...", is_master=True))
        job = Job(
            title="GenAI Architect",
            company="Acme Corp",
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
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_resume_pdf_defaults_to_inline_disposition(client):
    response = client.get("/jobs/1/resume.pdf")
    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith("inline;")
    assert "Resume_Jane_Doe_GenAI_Architect_Acme_Corp.pdf" in response.headers["content-disposition"]


def test_resume_pdf_download_true_forces_attachment_disposition(client):
    response = client.get("/jobs/1/resume.pdf?download=true")
    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith("attachment;")


def test_cover_letter_pdf_download_true_forces_attachment_disposition(client):
    response = client.get("/jobs/1/cover-letter.pdf?download=true")
    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith("attachment;")
    assert "CL_Jane_Doe_GenAI_Architect_Acme_Corp.pdf" in response.headers["content-disposition"]
