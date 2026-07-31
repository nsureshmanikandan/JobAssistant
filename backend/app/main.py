from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import init_db
from app.scheduler import start_scheduler
from app.api import jobs, search_runs, applications, settings as settings_api, observability


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield


app = FastAPI(title="Job Application Assistant", lifespan=lifespan)

# Regex (not a fixed port list) because this is a single-user local tool and the
# frontend dev port varies (5173 by default, but shifts to avoid clashing with
# other local projects' dev servers).
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(search_runs.router)
app.include_router(applications.router)
app.include_router(settings_api.router)
app.include_router(observability.router)


@app.get("/health")
def health():
    return {"status": "ok"}
