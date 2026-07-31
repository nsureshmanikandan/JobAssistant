from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    company: str
    location: str
    salary_text: Optional[str] = None
    source_url: str
    source_site: str
    description: Optional[str] = None
    needs_manual_paste: bool = False
    dedupe_key: str = Field(index=True, unique=True)
    match_percentage: Optional[int] = None
    matched_skills: Optional[str] = None   # JSON-encoded list
    missing_skills: Optional[str] = None   # JSON-encoded list
    sponsorship_required: Optional[bool] = None
    company_size_estimate: Optional[str] = None
    scoring_reasoning: Optional[str] = None
    status: str = "pending_review"  # pending_review|scoring_failed|approved|rejected|applied
    tailored_resume: Optional[str] = None
    tailored_cover_letter: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class ResumeVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    label: str
    content: str
    is_master: bool = False
    created_at: datetime = Field(default_factory=utcnow)


class Application(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    status: str = "approved"  # approved|applied|skipped
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class SearchRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=utcnow)
    finished_at: Optional[datetime] = None
    jobs_found: int = 0
    jobs_new: int = 0
    status: str = "running"  # running|completed|failed
    error: Optional[str] = None


class SearchCriteria(SQLModel, table=True):
    # Single-row table (id always 1) — editable via Settings, replacing what
    # used to be a hardcoded string duplicated across three backend files.
    id: Optional[int] = Field(default=None, primary_key=True)
    titles: str = "AI Senior Technical Project Manager,GenAI Architect,Agentic AI Architect"  # comma-separated
    location: str = "Chennai"
    fte_only: bool = True
    salary_min_lakhs: int = 45
    salary_max_lakhs: int = 60
    industry: str = "MNC"
    min_company_size: int = 5000
    exclude_sponsorship: bool = True
    updated_at: datetime = Field(default_factory=utcnow)


class LLMCallLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str
    model: str
    prompt_id: str
    job_id: Optional[int] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    latency_ms: Optional[int] = None
    success: bool = True
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
