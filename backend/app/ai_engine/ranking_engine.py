
def rank_job_matches(matches: list[dict]) -> list[dict]:
    """
    Rank jobs using skill-match score and eligibility status.
    This is a transparent sorting rule, not an AI hiring prediction.
    """

    eligibility_priority = {
        "eligible": 0,
        "review_required": 1,
        "not_eligible": 2,
    }

    ranked = sorted(
        matches,
        key=lambda item: (
            eligibility_priority.get(
                item.get("eligibility_status", "review_required"),
                1,
            ),
            -float(item.get("score") or 0),
            item.get("title") or "",
        ),
    )

    for position, item in enumerate(ranked, start=1):
        item["rank"] = position

    return ranked


def explain_job_match(match: dict) -> dict:
    score = float(match.get("score") or 0)
    matched = match.get("matched_skills") or []
    missing = match.get("missing_skills") or []
    eligibility = match.get("eligibility_status") or "review_required"

    if score >= 80:
        score_label = "Strong skill overlap"
    elif score >= 60:
        score_label = "Good skill overlap"
    elif score >= 40:
        score_label = "Partial skill overlap"
    else:
        score_label = "Low skill overlap"

    return {
        "score": score,
        "score_label": score_label,
        "eligibility_status": eligibility,
        "matched_skill_count": len(matched),
        "missing_skill_count": len(missing),
        "matched_skills": matched,
        "missing_skills": missing,
        "explanation": (
            f"{len(matched)} skills matched and "
            f"{len(missing)} identified skills are missing. "
            f"Eligibility screening status: {eligibility}."
        ),
        "is_hiring_probability": False,
    }
