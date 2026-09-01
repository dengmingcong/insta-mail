from fastapi import APIRouter

from src.adapters.vesync.projects.router import router as projects_router
from src.adapters.vesync.zentao.router import router as zentao_router

router = APIRouter(prefix="/vesync")
router.include_router(projects_router)
router.include_router(zentao_router)
