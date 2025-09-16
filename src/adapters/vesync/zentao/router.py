"""Core of zentao with all the endpoints."""

import requests
from fastapi import APIRouter

from src.adapters.vesync.zentao.service import (
    get_one_project_by_name,
    get_project_bugs,
    signin_zentao,
)

router = APIRouter(prefix="/zentao")


@router.get("/bugs")
def read_project_bugs(project_name: str) -> list[dict]:
    """Get bugs for a specific project.

    :param project_name: The name of the project in zentao.
    """
    # Init requests session.
    session = requests.Session()

    # Log into zentao.
    signin_zentao(session, "raigordeng", "111111a?D")

    # Filter project by name.
    project: dict = get_one_project_by_name(session, project_name)

    # Get bugs for the project.
    return get_project_bugs(session, project["id"])
