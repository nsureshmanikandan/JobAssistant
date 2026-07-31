import json
from dataclasses import dataclass
from app.llm.base import LLMProvider
from app.prompts.tailoring import TAILORING_SYSTEM_PROMPT, build_tailoring_prompt


@dataclass
class TailoredContent:
    tailored_resume: str
    cover_letter: str


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
