import json
import pytest
from app.services.tailoring import tailor_job, TailoredContent
from app.llm.base import LLMResponse


class FakeLLM:
    name = "fake"

    def __init__(self, response_text: str) -> None:
        self._response_text = response_text

    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return LLMResponse(text=self._response_text, tokens_in=10, tokens_out=20, model="fake-model")


@pytest.mark.asyncio
async def test_tailor_job_parses_valid_json():
    payload = {"tailored_resume": "SUMMARY\n...", "cover_letter": "Dear Hiring Manager,\n..."}
    llm = FakeLLM(json.dumps(payload))
    result = await tailor_job(
        llm, resume="resume text", job_description="jd", job_title="GenAI Architect", company="Acme"
    )
    assert isinstance(result, TailoredContent)
    assert result.tailored_resume.startswith("SUMMARY")
    assert "Dear Hiring Manager" in result.cover_letter
