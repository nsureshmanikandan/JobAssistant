import json
from dataclasses import dataclass
from datetime import date
from app.llm.base import LLMProvider
from app.prompts.tailoring import TAILORING_SYSTEM_PROMPT, build_tailoring_prompt


@dataclass
class TailoredContent:
    tailored_resume: str
    cover_letter: str


def extract_candidate_name(resume_text: str) -> str:
    """First non-blank line of the master resume — same heuristic the frontend's
    ResumePreview component uses to render the name as a heading."""
    for line in resume_text.split("\n"):
        stripped = line.strip()
        if stripped:
            return stripped
    return "Candidate"


def build_cover_letter_header(
    candidate_name: str, candidate_location: str, company: str, job_location: str, role_title: str
) -> str:
    today = date.today().strftime("%B %d, %Y")
    return (
        f"{candidate_name}\n"
        f"{candidate_location}\n"
        f"{today}\n"
        "\n"
        "Hiring Manager\n"
        f"{company}\n"
        f"{job_location}\n"
        "\n"
        f"Subject: Application for {role_title} Position\n"
    )


async def tailor_job(
    llm: LLMProvider, resume: str, job_description: str, job_title: str, company: str
) -> TailoredContent:
    prompt = build_tailoring_prompt(
        resume=resume, job_description=job_description, job_title=job_title, company=company
    )
    response = await llm.complete(TAILORING_SYSTEM_PROMPT, prompt)
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM did not return valid JSON: {exc}") from exc
    return TailoredContent(
        tailored_resume=data["tailored_resume"],
        cover_letter=data["cover_letter"],
    )
