import json
import pytest
from app.services.tailoring import (
    tailor_job, TailoredContent, extract_candidate_name, build_cover_letter_header, build_pdf_filename,
)
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


def test_extract_candidate_name_returns_first_nonblank_line():
    resume = "\n\nSURESH MANIKANDAN NATARAJAN\nAgentic AI Architect\n..."
    assert extract_candidate_name(resume) == "SURESH MANIKANDAN NATARAJAN"


def test_extract_candidate_name_falls_back_when_resume_empty():
    assert extract_candidate_name("   \n  \n") == "Candidate"


def test_build_cover_letter_header_includes_all_fields():
    header = build_cover_letter_header(
        candidate_name="Suresh Manikandan Natarajan",
        candidate_location="Chennai",
        company="Acme Corp",
        job_location="Chennai",
        role_title="GenAI Architect",
    )
    assert "Suresh Manikandan Natarajan" in header
    assert "Chennai" in header
    assert "Acme Corp" in header
    assert "Subject: Application for GenAI Architect Position" in header
    assert "Hiring Manager" in header


def test_build_pdf_filename_sanitizes_and_joins_parts():
    filename = build_pdf_filename(
        "Resume", "Suresh Manikandan Natarajan", "Lead Agentic AI Engineer", "Trimble Inc."
    )
    assert filename == "Resume_Suresh_Manikandan_Natarajan_Lead_Agentic_AI_Engineer_Trimble_Inc.pdf"


def test_build_pdf_filename_handles_commas_and_slashes():
    filename = build_pdf_filename("CL", "Jane Doe", "Program Manager/Senior Member, GenAI", "D. E. Shaw")
    assert filename == "CL_Jane_Doe_Program_Manager_Senior_Member_GenAI_D_E_Shaw.pdf"
    assert "/" not in filename and "," not in filename
