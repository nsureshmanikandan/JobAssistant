from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# One Paragraph flowable per line (not Preformatted, which does NOT wrap and
# runs long lines off the page edge) so text word-wraps within the margins.
# Single-column, no tables/floats — deliberately plain so ATS parsers (which
# strip PDF layout and read raw text) don't mis-order content.
#
# Standalone all-caps lines (SUMMARY, EXPERIENCE, SKILLS, EDUCATION — the
# section headers the tailoring prompt is instructed to produce) are bolded
# so the document reads as a resume's section structure rather than one flat
# block of prose. This is purely a font-weight/size difference, which ATS
# text extraction ignores, so it doesn't compromise ATS-safety.


def _is_section_header(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and stripped.isupper() and len(stripped) > 1


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
    heading_style = ParagraphStyle(
        "SectionHeader", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=12, spaceBefore=10, spaceAfter=4,
    )
    body_style = styles["Normal"]

    story = []
    for line in text.split("\n"):
        if line.strip() == "":
            story.append(Spacer(1, 6))
        elif _is_section_header(line):
            story.append(Paragraph(escape(line.strip()), heading_style))
        else:
            story.append(Paragraph(escape(line), body_style))
    doc.build(story)
    return buffer.getvalue()


def render_resume_pdf(tailored_resume: str) -> bytes:
    return _text_to_pdf(tailored_resume)


def render_cover_letter_pdf(cover_letter: str) -> bytes:
    return _text_to_pdf(cover_letter)
