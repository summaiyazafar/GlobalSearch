from app.ai_engine.skill_extractor import extract_skills


def build_tailored_resume_text(
    original_text: str,
    job_title: str,
    company: str | None,
) -> dict:
    """
    Prepare an ATS-oriented copy using verified information
    from the user's original resume.

    Original factual statements are preserved. Missing job skills
    are reported separately and never added as user qualifications.
    """

    original_text = (original_text or "").strip()

    if not original_text:
        raise ValueError("Original resume text is empty.")

    resume_skills = extract_skills(original_text)

    tailored_text = (
        f"TARGET ROLE: {job_title}\n"
        f"TARGET COMPANY: {company or 'Not specified'}\n\n"
        "ORIGINAL RESUME CONTENT\n"
        "=======================\n\n"
        f"{original_text}\n"
    )

    return {
        "title": f"Resume - {job_title}",
        "content": tailored_text,
        "verified_skills": resume_skills,
        "preservation_note": (
            "Original resume statements have been retained. "
            "No missing skills or unverified qualifications "
            "have been added."
        ),
    }


def build_cover_letter(
    job_title: str,
    company: str | None,
    resume_text: str,
    matched_skills: list[str],
) -> str:
    """
    Build a conservative cover letter using only information
    available in the supplied resume and job record.
    """

    company_name = company or "the hiring team"

    if matched_skills:
        skill_sentence = (
            "My resume includes experience or skills related to "
            + ", ".join(matched_skills)
            + "."
        )
    else:
        skill_sentence = (
            "I would welcome the opportunity to discuss how "
            "my background relates to this position."
        )

    return f"""Dear Hiring Team,

I am writing to express my interest in the {job_title} position at {company_name}.

{skill_sentence}

I would appreciate the opportunity to discuss my background and how it may align with the requirements of this role. Thank you for considering my application.

Kind regards,
[Your Name]
"""