import json
import pytest
from app.services.scoring import score_job, ScoreResult
from app.llm.base import LLMResponse


class FakeLLM:
    name = "fake"

    def __init__(self, response_text: str) -> None:
        self._response_text = response_text

    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return LLMResponse(text=self._response_text, tokens_in=10, tokens_out=20, model="fake-model")


@pytest.mark.asyncio
async def test_score_job_parses_valid_json():
    payload = {
        "match_percentage": 90,
        "matched_skills": ["Python", "LLM orchestration"],
        "missing_skills": ["Kubernetes"],
        "sponsorship_required": False,
        "company_size_estimate": "10000+",
        "reasoning": "Strong alignment on GenAI architecture experience.",
    }
    llm = FakeLLM(json.dumps(payload))
    result = await score_job(llm, resume="resume text", job_description="jd text", criteria="criteria text")
    assert isinstance(result, ScoreResult)
    assert result.match_percentage == 90
    assert result.sponsorship_required is False


@pytest.mark.asyncio
async def test_score_job_raises_on_malformed_json():
    llm = FakeLLM("not json at all")
    with pytest.raises(ValueError, match="did not return valid JSON"):
        await score_job(llm, resume="r", job_description="j", criteria="c")
