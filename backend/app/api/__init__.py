from fastapi import APIRouter
from app.api.tenders import router as tenders_router
from app.api.actions import router as actions_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(tenders_router)
api_router.include_router(actions_router)
