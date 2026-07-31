# Job Application Assistant — Design Spec

Date: 2026-07-31
Status: Approved (verbal + credential hand-off from user)

## Purpose

Automate the daily grind of finding and preparing applications for senior GenAI/Agentic-AI
roles, while keeping the final "submit" action always in the user's hands.

**Target criteria (seeded into Settings on first run):**
- Titles: AI Senior Technical Project Manager, GenAI Architect, Agentic AI Architect
- Location: Chennai, India — FTE only
- Salary: ₹45L – ₹60L
- Industry: MNC only
- Company size: ≥ 5000 employees (skip smaller)
- Skip roles requiring visa/work sponsorship
- Match threshold: ≥ 85% fit against master resume (configurable)

## Architecture

Monorepo at `C:\Users\n.sureshmanikandan\Repo1\JobAssistant`:

```
/backend    Python FastAPI + APScheduler
/frontend   React + Vite + TypeScript + Tailwind
/infra      Docker Compose (local) + Azure Container Apps manifests (phase 2)
/docs
```

## Backend Components

- **`core/search_providers/`** — `SearchProvider` interface. Implementations:
  `AzureBingSearchProvider`, `GoogleCustomSearchProvider`. Selected via `SEARCH_PROVIDER` env var.
  Queries use `site:linkedin.com/jobs`, `site:naukri.com`, `site:indeed.com` filters,
  restricted to postings from the last 24 hours.
- **`core/llm_providers/`** — `LLMProvider` interface. Implementations: `AzureOpenAIProvider`
  (gpt-5.4-mini via Azure AI Foundry), `ClaudeProvider`, `GeminiProvider` (gemini-3.1-flash-lite
  via AI Studio API key — Vertex/ADC is not used, per prior finding that Vertex AI is blocked by
  Accenture IAM). Selected via `LLM_PROVIDER` env var, swappable without code changes.
- **`core/job_fetcher.py`** — fetches each result's public posting page (httpx + readability
  parsing). If blocked (403/Cloudflare — common on LinkedIn), stores a stub with
  title/company/URL from the search snippet and flags `needs_manual_paste`.
- **`core/scoring.py`** — LLM call, **structured JSON output**
  (`match_percentage`, `matched_skills`, `missing_skills`, `sponsorship_required`,
  `company_size_estimate`, `reasoning`) scored against the master resume + Settings criteria.
  Sponsorship detection is an explicit field the LLM must populate, not an afterthought —
  this was a hard requirement in the original ask and false negatives here waste the user's time.
- **`core/tailoring.py`** — generates tailored resume bullets + cover letter. Runs **on-demand**
  only when the user opens a job for review (not for every discovered job), to control LLM cost.
  Explicit "Regenerate" action re-runs it; opening the same job again does not.
- **`core/export.py`** — renders the tailored resume and cover letter to **PDF** via ReportLab
  (pure-Python, no native system libraries required — WeasyPrint was considered but needs GTK/
  Pango installed at the OS level, which fails on a plain Windows dev machine), ATS-safe
  single-column layout — no tables/text-boxes/columns that break ATS parsers. This is required
  for Phase 1, not deferred: the user needs an actual file to attach when submitting on the job
  site, not just on-screen text.
- **`core/scheduler.py`** — APScheduler daily job (default 07:00 local) runs discovery across
  target titles, dedupes against history (idempotent — a second run same day only processes new
  postings), fetches, scores, stores results. Manual "Run search now" button available too.
- **`prompts/`** — versioned prompt templates (scoring, tailoring, cover letter) as separate
  files, each with a `prompt_id`, so observability can attribute results to a specific version.
- **`db/`** — SQLite via SQLModel: `Job`, `ResumeVersion`, `Application`, `SearchRun`,
  `LLMCallLog` tables.
- **`observability/`** — structured JSON logging (structlog) + OpenTelemetry instrumentation on
  every HTTP request and every LLM/search call (provider, model, prompt_id, tokens in/out, cost
  estimate, latency, success/failure). Exports to console locally; to Azure Application Insights
  when deployed to cloud (phase 2).

## Frontend (React + Vite + Tailwind)

- **Dashboard** — pending jobs from the last run: match %, company, title, salary, sponsorship
  flag, source site, "needs manual paste" indicator.
- **Job review panel** — full JD, tailored resume diff, editable cover letter draft,
  Approve / Reject / Regenerate buttons, **Download Resume PDF** / **Download Cover Letter PDF**
  buttons (enabled once the user is happy with the edited text).
- **Manual paste-in form** — paste a URL or raw JD text anytime, outside the daily run.
- **Application history** — status per job over time: Pending → Approved → Applied →
  (or Rejected / Skipped).
- **Settings** — edit search criteria, view active LLM/search provider (read-only — keys are
  never entered or displayed in the UI), manage master resume.
- **Observability tab** — recent LLM calls (cost/latency/provider/prompt version), daily search
  run history/status.

## Data Flow & the Approval Gate

Discover (search API) → fetch public page → LLM structured match-score against criteria →
surfaces in dashboard if match ≥ threshold AND `sponsorship_required == false` → user opens it →
tailoring generates resume/cover letter → user edits inline → user downloads the PDF resume and
cover letter → **user clicks Approve** → the job's actual application URL opens in a new tab for
the **user to fill in (attaching the downloaded PDFs) and submit themselves**.

This is a hard boundary: no automation in this system fills out or submits a job application
form on the user's behalf. The tool's job stops at "here are your tailored materials and the
link."

## Error Handling

- Search quota exceeded → banner + graceful halt, logged, resumes next scheduled run.
- Fetch blocked → stub + manual-paste prompt.
- LLM timeout/error → one retry with backoff, else flagged `scoring_failed` for manual retry.
- Duplicate postings (re-runs, cross-site) → deduped by normalized
  `hash(company + title + location)`.

## Secrets Handling

- All provider keys live in a single `.env` file at the project root, created locally, never
  committed. `.gitignore` excludes `.env`, `*.db`, `__pycache__/`, `node_modules/`.
- `.env.example` documents required variable names with no real values.
- Cloud phase (2) moves these into Azure Key Vault references instead of plain env vars.

## Testing

- Backend: pytest for each search/LLM adapter (mocked), job_fetcher parsing (fixture HTML),
  dedupe logic, scoring JSON-schema validation.
- Frontend: Vitest + React Testing Library for dashboard/review components; one Playwright
  smoke test for the approve flow (stops before any real submit).
- Manual: one real end-to-end search cycle reviewed before calling phase 1 done.

## Deployment

- **Phase 1 (this build)**: `docker-compose up` — backend + frontend + SQLite volume, runs
  entirely on the user's machine.
- **Phase 2 (later)**: Azure Container Apps manifests + GitHub Actions (build → ACR → deploy) +
  Key Vault, so the daily search runs even when the laptop is off.

## Out of Scope (this phase)

- Automated form-filling or submission on any job site (safety boundary, not a technical gap).
- LinkedIn/Naukri authenticated scraping (ToS/ban risk — explicitly rejected in favor of search
  API + public-page fetch + manual paste).
- DOCX export (PDF only for Phase 1 — DOCX can be added later without architecture changes if
  a specific ATS rejects PDFs).
