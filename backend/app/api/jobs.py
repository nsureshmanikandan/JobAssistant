import time
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import Job, ResumeVersion, Application
from app.llm.factory import get_llm_provider
from app.services.tailoring import tailor_job
from app.services.export import render_resume_pdf, render_cover_letter_pdf
from app.services.dedupe import job_dedupe_key
from app.observability.llm_log import log_llm_call
from app.prompts.tailoring import TAILORING_PROMPT_ID

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
def list_jobs(session: Session = Depends(get_session)):
    jobs = session.exec(select(Job).order_by(Job.created_at.desc())).all()
    return jobs


@router.get("/{job_id}")
def get_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/manual")
def create_manual_job(payload: dict, session: Session = Depends(get_session)):
    key = job_dedupe_key(
        company=payload["company"], title=payload["title"], location=payload.get("location", "Chennai")
    )
    job = Job(
        title=payload["title"],
        company=payload["company"],
        location=payload.get("location", "Chennai"),
        source_url=payload["source_url"],
        source_site="manual",
        description=payload.get("description") or None,
        needs_manual_paste=not bool(payload.get("description")),
        dedupe_key=key,
        status="pending_review",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@router.post("/{job_id}/tailor")
async def tailor(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.description is None:
        raise HTTPException(status_code=400, detail="Job has no description yet — paste one first")

    master = session.exec(select(ResumeVersion).where(ResumeVersion.is_master.is_(True))).first()
    if master is None:
        raise HTTPException(status_code=400, detail="No master resume configured in Settings")

    llm = get_llm_provider()
    start = time.monotonic()
    success = True
    error = None
    try:
        result = await tailor_job(
            llm, resume=master.content, job_description=job.description, job_title=job.title, company=job.company
        )
    except ValueError as exc:
        success = False
        error = str(exc)
        raise HTTPException(status_code=502, detail=f"Tailoring failed: {exc}") from exc
    finally:
        latency_ms = int((time.monotonic() - start) * 1000)
        log_llm_call(
            session, provider=llm.name, model=getattr(llm, "_deployment", llm.name),
            prompt_id=TAILORING_PROMPT_ID, job_id=job_id, tokens_in=0, tokens_out=0,
            latency_ms=latency_ms, success=success, error=error,
        )

    job.tailored_resume = result.tailored_resume
    job.tailored_cover_letter = result.cover_letter
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@router.get("/{job_id}/resume.pdf")
def download_resume_pdf(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job is None or job.tailored_resume is None:
        raise HTTPException(status_code=404, detail="No tailored resume for this job yet")
    pdf_bytes = render_resume_pdf(job.tailored_resume)
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.get("/{job_id}/cover-letter.pdf")
def download_cover_letter_pdf(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job is None or job.tailored_cover_letter is None:
        raise HTTPException(status_code=404, detail="No cover letter for this job yet")
    pdf_bytes = render_cover_letter_pdf(job.tailored_cover_letter)
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.post("/{job_id}/approve")
def approve_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "approved"
    session.add(job)
    session.add(Application(job_id=job_id, status="approved"))
    session.commit()
    session.refresh(job)
    return job


@router.post("/{job_id}/reject")
def reject_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "rejected"
    session.add(job)
    session.commit()
    session.refresh(job)
    return job
