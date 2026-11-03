from io import BytesIO

from docx import Document
from docx.shared import Inches, Pt


def export_resume_to_docx(
    resume_text: str,
    document_title: str = "Tailored Resume",
) -> bytes:
    """
    Export prepared resume text to a DOCX document.
    """

    document = Document()

    section = document.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    styles = document.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10)

    document.add_heading(document_title, level=0)

    for line in resume_text.splitlines():
        clean_line = line.strip()

        if not clean_line:
            continue

        if clean_line.isupper() and len(clean_line) < 90:
            document.add_heading(clean_line, level=1)
        else:
            document.add_paragraph(clean_line)

    output = BytesIO()
    document.save(output)

    return output.getvalue()