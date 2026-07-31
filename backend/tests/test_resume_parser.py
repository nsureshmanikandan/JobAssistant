import pytest
from io import BytesIO
from docx import Document as DocxDocument
from app.services.resume_parser import parse_docx, parse_resume_file


def _make_docx_bytes(paragraphs: list[str]) -> bytes:
    doc = DocxDocument()
    for p in paragraphs:
        doc.add_paragraph(p)
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def test_parse_docx_extracts_paragraph_text():
    file_bytes = _make_docx_bytes(["SUMMARY", "Senior GenAI Architect with 10 years experience."])
    text = parse_docx(file_bytes)
    assert "SUMMARY" in text
    assert "Senior GenAI Architect" in text


def test_parse_resume_file_rejects_unsupported_extension():
    with pytest.raises(ValueError, match="Unsupported resume file type"):
        parse_resume_file("resume.txt", b"plain text")


def test_parse_resume_file_dispatches_docx():
    file_bytes = _make_docx_bytes(["EDUCATION", "B.E. Computer Science"])
    text = parse_resume_file("resume.docx", file_bytes)
    assert "EDUCATION" in text
