from io import BytesIO
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from docx import Document as DocxDocument
from app.main import app
from app.db import session as db_session


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
    yield TestClient(app)
    app.dependency_overrides.clear()


def _docx_bytes(paragraphs: list[str]) -> bytes:
    doc = DocxDocument()
    for p in paragraphs:
        doc.add_paragraph(p)
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def test_upload_docx_resume_sets_master(client):
    file_bytes = _docx_bytes(["SUMMARY", "Senior GenAI Architect."])
    response = client.post(
        "/settings/resume/upload",
        files={"file": ("resume.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 200
    body = response.json()
    assert "Senior GenAI Architect" in body["content"]
    assert body["is_master"] is True


def test_upload_unsupported_file_type_rejected(client):
    response = client.post(
        "/settings/resume/upload",
        files={"file": ("resume.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 400
