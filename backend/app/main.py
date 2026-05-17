from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.api import api_router
from app.tasks.scheduler import start_scheduler, stop_scheduler

settings = get_settings()
configure_logging(settings.ENVIRONMENT)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_starting", environment=settings.ENVIRONMENT)
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("app_stopped")


app = FastAPI(
    title="Etimad Tenders Monitor",
    description="Automated Saudi Etimad tenders monitoring with AI matching and email alerts",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "etimad-monitor"}
