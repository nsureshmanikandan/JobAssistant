from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Preformatted

# Preformatted renders a single-column, monospace text block with no tables,
# floats, or multi-column layout — deliberately plain so ATS parsers (which
# strip PDF layout and read raw text) don't mis-order content.


def _text_to_pdf(text: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    doc.build([Preformatted(text, styles["Normal"])])
    return buffer.getvalue()


def render_resume_pdf(tailored_resume: str) -> bytes:
    return _text_to_pdf(tailored_resume)


def render_cover_letter_pdf(cover_letter: str) -> bytes:
    return _text_to_pdf(cover_letter)
