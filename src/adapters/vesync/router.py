from fastapi import APIRouter

from src.adapters.vesync.projects import router as vesync_projects_router

vesync_router = APIRouter(prefix="/vesync", tags=["vesync"])
vesync_router.include_router(vesync_projects_router)
