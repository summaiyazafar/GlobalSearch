
from pathlib import Path
from playwright.async_api import Page


ALLOWED_EXTENSIONS = {".pdf", ".docx"}


async def upload_resume(
    page: Page,
    file_path: str,
    selector: str = "input[type='file']",
) -> dict:

    resume_path = Path(file_path).resolve()

    if not resume_path.exists() or not resume_path.is_file():
        raise FileNotFoundError("Resume file was not found.")

    if resume_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Only PDF and DOCX resumes are supported.")

    file_input = page.locator(selector).first

    if await file_input.count() == 0:
        raise ValueError("Resume upload field was not found.")

    await file_input.set_input_files(str(resume_path))

    return {
        "success": True,
        "filename": resume_path.name,
        "message": "Resume attached. Review the application before submission.",
    }
