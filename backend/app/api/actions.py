from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.logging import get_logger
from app.tasks.scrape_task import run_scrape_job, run_matching_job, run_notification_job

logger = get_logger(__name__)
router = APIRouter(tags=["actions"])

_running_jobs: dict[str, bool] = {"scrape": False, "matching": False}


class JobResponse(BaseModel):
    status: str
    message: str
    job_id: Optional[int] = None


async def _run_scrape_bg():
    _running_jobs["scrape"] = True
    try:
        await run_scrape_job()
    finally:
        _running_jobs["scrape"] = False


async def _run_matching_bg():
    _running_jobs["matching"] = True
    try:
        await run_matching_job()
        await run_notification_job()
    finally:
        _running_jobs["matching"] = False


@router.post("/scrape/run", response_model=JobResponse)
async def trigger_scrape(background_tasks: BackgroundTasks):
    if _running_jobs.get("scrape"):
        raise HTTPException(status_code=409, detail="Scrape job already running")
    background_tasks.add_task(_run_scrape_bg)
    return JobResponse(status="started", message="Scrape job started in background")


@router.post("/matching/run", response_model=JobResponse)
async def trigger_matching(background_tasks: BackgroundTasks):
    if _running_jobs.get("matching"):
        raise HTTPException(status_code=409, detail="Matching job already running")
    background_tasks.add_task(_run_matching_bg)
    return JobResponse(status="started", message="Matching and notification job started")


@router.get("/jobs/status")
async def jobs_status():
    return {
        "scrape_running": _running_jobs.get("scrape", False),
        "matching_running": _running_jobs.get("matching", False),
    }
