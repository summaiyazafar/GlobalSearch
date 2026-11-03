from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_RESUME_SIZE = 10 * 1024 * 1024


class ResumeParsingError(Exception):
    """Raised when a resume cannot be parsed safely."""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(file_bytes))

        if reader.is_encrypted:
            raise ResumeParsingError(
                "Password-protected PDF files are not supported."
            )

        pages = []

        for page in reader.pages:
            pages.append(page.extract_text() or "")

        return "\n".join(pages).strip()

    except ResumeParsingError:
        raise
    except Exception as exc:
        raise ResumeParsingError(
            "Could not read the PDF file."
        ) from exc


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        document = Document(BytesIO(file_bytes))

        paragraphs = [
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        table_text = []

        for table in document.tables:
            for row in table.rows:
                cells = [
                    cell.text.strip()
                    for cell in row.cells
                    if cell.text.strip()
                ]

                if cells:
                    table_text.append(" | ".join(cells))

        return "\n".join(paragraphs + table_text).strip()

    except Exception as exc:
        raise ResumeParsingError(
            "Could not read the DOCX file."
        ) from exc


def extract_text_from_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8-sig").strip()
    except UnicodeDecodeError:
        try:
            return file_bytes.decode("utf-8", errors="replace").strip()
        except Exception as exc:
            raise ResumeParsingError(
                "Could not read the text file."
            ) from exc


def extract_resume_text(
    filename: str,
    file_bytes: bytes,
) -> str:
    """
    Extract text from PDF, DOCX, or TXT resumes.
    """

    if not filename:
        raise ResumeParsingError("A filename is required.")

    if len(file_bytes) > MAX_RESUME_SIZE:
        raise ResumeParsingError(
            "Resume file exceeds the 10 MB size limit."
        )

    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ResumeParsingError(
            "Unsupported file format. Upload PDF, DOCX, or TXT."
        )

    if not file_bytes:
        raise ResumeParsingError("The uploaded file is empty.")

    if extension == ".pdf":
        extracted_text = extract_text_from_pdf(file_bytes)

    elif extension == ".docx":
        extracted_text = extract_text_from_docx(file_bytes)

    else:
        extracted_text = extract_text_from_txt(file_bytes)

    if not extracted_text:
        raise ResumeParsingError(
            "No readable text was found. Scanned PDFs may need OCR."
        )

    return extracted_text