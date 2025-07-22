from fastapi import APIRouter

from src.adapters.vesync.projects.router import router as projects_router

router = APIRouter(prefix="/vesync")
router.include_router(projects_router)
