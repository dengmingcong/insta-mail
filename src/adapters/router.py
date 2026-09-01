from fastapi import APIRouter

from src.adapters.allure.router import router as allure_router
from src.adapters.vesync.router import router as vesync_router

router = APIRouter(prefix="/adapters", tags=["adapters"])
router.include_router(vesync_router)
router.include_router(allure_router)
