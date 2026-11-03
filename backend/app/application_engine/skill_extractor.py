import re
from collections import defaultdict


SKILL_ALIASES = {
    "python": ["python", "python 3"],
    "sql": ["sql", "structured query language"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "dl"],
    "data science": ["data science"],
    "data analysis": ["data analysis", "data analytics"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch", "torch"],
    "opencv": ["opencv", "open cv"],
    "computer vision": ["computer vision", "cv"],
    "natural language processing": ["natural language processing", "nlp"],
    "generative ai": ["generative ai", "genai", "gen ai"],
    "large language models": ["large language model", "large language models", "llm", "llms"],
    "prompt engineering": ["prompt engineering"],
    "langchain": ["langchain"],
    "retrieval augmented generation": ["retrieval augmented generation", "rag"],
    "faiss": ["faiss"],
    "pinecone": ["pinecone"],
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "streamlit": ["streamlit"],
    "django": ["django"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "react.js"],
    "next.js": ["next.js", "nextjs"],
    "node.js": ["node.js", "nodejs"],
    "html": ["html"],
    "css": ["css"],
    "git": ["git"],
    "github": ["github"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud platform"],
    "power bi": ["power bi", "powerbi"],
    "tableau": ["tableau"],
    "excel": ["excel", "microsoft excel"],
    "matplotlib": ["matplotlib"],
    "seaborn": ["seaborn"],
    "statistics": ["statistics", "statistical analysis"],
    "data visualization": ["data visualization", "data visualisation"],
    "api development": ["api development", "rest api", "restful api"],
    "playwright": ["playwright"],
    "selenium": ["selenium"],
    "n8n": ["n8n"],
    "zapier": ["zapier"],
    "automation": ["automation", "workflow automation"],
    "postgresql": ["postgresql", "postgres"],
    "mysql": ["mysql"],
    "mongodb": ["mongodb"],
    "redis": ["redis"],
    "linux": ["linux"],
    "agile": ["agile"],
    "scrum": ["scrum"],
}


def _contains_term(text: str, term: str) -> bool:
    """
    Match a phrase without matching it inside unrelated words.
    """
    pattern = r"(?<![a-zA-Z0-9])" + re.escape(term) + r"(?![a-zA-Z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def extract_skills(text: str) -> list[str]:
    """
    Extract recognized technical skills from resume or job text.

    This is a dictionary-based baseline, not an exhaustive NLP model.
    """
    if not text:
        return []

    normalized_text = text.lower()
    found = []

    for canonical_name, aliases in SKILL_ALIASES.items():
        if any(_contains_term(normalized_text, alias) for alias in aliases):
            found.append(canonical_name)

    return sorted(set(found))


def extract_skill_evidence(text: str) -> dict[str, list[str]]:
    """
    Return matched skill names and short source snippets.
    """
    if not text:
        return {}

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    evidence = defaultdict(list)

    for line in lines:
        for skill in extract_skills(line):
            if len(evidence[skill]) < 3:
                evidence[skill].append(line[:300])

    return dict(evidence)