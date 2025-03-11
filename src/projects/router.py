"""Core of projects with all the endpoints."""

import datetime

import requests
from fastapi import APIRouter

from src.projects import constants as project_constants
from src.projects import service as project_service
from src.projects.schemas import PMProject

router = APIRouter(
    tags=["projects"],
)


@router.get("/projects")
async def read_projects(
    title_like: str, page_number: int = 1, page_size: int = 50
) -> list[PMProject]:
    """Query projects by matching the title.

    :param title_like: Title to match.
    :param page_number: Page number.
    :param page_size: Page size.
    """
    cookies: dict = project_service.auth_pm()

    response = requests.post(
        project_constants.VesyncService.PM_API_ORIGIN
        + project_constants.VesyncService.API_PATH,
        json={
            "context": {
                **project_constants.VesyncService.API_CONTEXT,
                "accountID": cookies["userId"],
                "token": cookies["token"],
                "traceId": int(datetime.datetime.now().timestamp()),
            },
            "data": {
                "projectType": 1,
                "relatedToMe": False,
                "onlyCurrGroup": True,
                "projectStatus": [],
                "projectName": title_like,
                "pageNo": page_number,
                "pageSize": page_size,
            },
        },
    )

    return [
        PMProject(id=project["projectId"], name=project["projectFullName"])
        for project in response.json()["result"]["projectList"]
    ]
