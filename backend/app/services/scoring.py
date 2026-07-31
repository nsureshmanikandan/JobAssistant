import json
from dataclasses import dataclass
from app.llm.base import LLMProvider
from app.prompts.scoring import SCORING_SYSTEM_PROMPT, build_scoring_prompt


@dataclass
class ScoreResult:
    match_percentage: int
    matched_skills: list[str]
    missing_skills: list[str]
    sponsorship_required: bool
    company_size_estimate: str
    reasoning: str


async def score_job(llm: LLMProvider, resume: str, job_description: str, criteria: str) -> ScoreResult:
    prompt = build_scoring_prompt(resume=resume, job_description=job_description, criteria=criteria)
    response = await llm.complete(SCORING_SYSTEM_PROMPT, prompt)
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM did not return valid JSON: {exc}") from exc
    return ScoreResult(
        match_percentage=int(data["match_percentage"]),
        matched_skills=data.get("matched_skills", []),
        missing_skills=data.get("missing_skills", []),
        sponsorship_required=bool(data["sponsorship_required"]),
        company_size_estimate=data.get("company_size_estimate", "unknown"),
        reasoning=data.get("reasoning", ""),
    )
