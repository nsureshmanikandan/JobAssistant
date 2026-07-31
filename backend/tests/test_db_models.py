from sqlmodel import SQLModel, create_engine, Session
from app.db.models import Job, ResumeVersion, Application, SearchRun, LLMCallLog


def test_job_can_be_created_and_queried():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        job = Job(
            title="GenAI Architect",
            company="Acme Corp",
            location="Chennai",
            source_url="https://example.com/job/1",
            source_site="linkedin",
            dedupe_key="acme|genai architect|chennai",
            status="pending_review",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        assert job.id is not None
        fetched = session.get(Job, job.id)
        assert fetched.title == "GenAI Architect"
