from io import BytesIO
from docx import Document as DocxDocument
from pypdf import PdfReader


def parse_docx(file_bytes: bytes) -> str:
    document = DocxDocument(BytesIO(file_bytes))
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


def parse_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def parse_resume_file(filename: str, file_bytes: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".docx"):
        return parse_docx(file_bytes)
    if lower.endswith(".pdf"):
        return parse_pdf(file_bytes)
    raise ValueError(f"Unsupported resume file type: {filename} (only .docx and .pdf are supported)")
