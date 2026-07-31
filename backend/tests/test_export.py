from app.services.export import render_resume_pdf, render_cover_letter_pdf


def test_render_resume_pdf_returns_pdf_bytes():
    pdf_bytes = render_resume_pdf("SUMMARY\nSenior GenAI Architect with 10 years experience.")
    assert pdf_bytes[:4] == b"%PDF"


def test_render_cover_letter_pdf_returns_pdf_bytes():
    pdf_bytes = render_cover_letter_pdf("Dear Hiring Manager,\n\nI am writing to apply...")
    assert pdf_bytes[:4] == b"%PDF"
