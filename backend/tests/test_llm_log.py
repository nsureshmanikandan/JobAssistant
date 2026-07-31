from sqlmodel import SQLModel, create_engine, Session, select
from app.db.models import LLMCallLog
from app.observability.llm_log import log_llm_call


def test_log_llm_call_persists_row():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        log_llm_call(
            session,
            provider="azure_openai",
            model="gpt-5.4-mini",
            prompt_id="scoring-v1",
            job_id=None,
            tokens_in=100,
            tokens_out=50,
            latency_ms=1200,
            success=True,
        )
        rows = session.exec(select(LLMCallLog)).all()
        assert len(rows) == 1
        assert rows[0].prompt_id == "scoring-v1"
