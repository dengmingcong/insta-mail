"""Core of projects with all the endpoints."""

import datetime

import requests
from fastapi import APIRouter

from src.adapters.vesync.projects import constants as project_constants
from src.adapters.vesync.projects import service as project_service
from src.adapters.vesync.projects.models import (
    PmOtpRequest,
    PMProject,
    PMProjectLocator,
    UserCreate,
    UserPasswordAuthResult,
)
from src.adapters.vesync.projects.utils import get_role_members

router = APIRouter(prefix="/projects")


@router.post("/login")
def signin_pm(user_in: UserCreate) -> UserPasswordAuthResult:
    """Signin PM using Playwright.

    :param user_in: UserCreate containing username and password.
    :raises HTTPException: If login fails or MFA is required.
    """
    return project_service.auth_by_user_password(user_in)


@router.post("/otp")
def enter_otp(request: PmOtpRequest):
    """Enter OTP for MFA.

    :param request: PmOtpRequest containing session ID and OTP.
    """
    project_service.enter_otp(session_id=request.session_id, otp=request.otp)


@router.get("/")
async def read_projects(
    title_like: str | None = None, page_number: int = 1, page_size: int = 50
) -> list[PMProjectLocator]:
    """Query projects by matching the title.

    :param title_like: Title to match.
    :param page_number: Page number.
    :param page_size: Page size.
    """
    cookies: dict = project_service.auth_pm()

    response = requests.post(
        project_constants.VesyncService.PM_API_ORIGIN
        + project_constants.APIPath.SEARCH_PROJECTS,
        json={
            "context": {
                **project_constants.VesyncService.API_CONTEXT,
                "method": "pageProjectSummaryV2",
                "accountID": cookies["account_id"],
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
        PMProjectLocator(id=project["projectId"], title=project["projectFullName"])
        for project in response.json()["result"]["projectList"]
    ]


@router.get("/{project_id}")
async def read_project(project_id: int) -> PMProject:
    """Query project details by project ID.

    :param project_id: Project ID.
    """
    cookies: dict = project_service.auth_pm()

    response = requests.post(
        project_constants.VesyncService.PM_API_ORIGIN
        + project_constants.APIPath.GET_PROJECT_MEMBERS,
        json={
            "context": {
                **project_constants.VesyncService.API_CONTEXT,
                "method": "getRelatedProjectMember",
                "accountID": cookies["account_id"],
                "token": cookies["token"],
                "traceId": int(datetime.datetime.now().timestamp()),
            },
            "data": {"projectId": project_id},
        },
    )

    raw_members = response.json()["result"]["postMemberList"]

    return PMProject(
        project_managers=get_role_members(raw_members, "项目经理"),
        api_testers=get_role_members(raw_members, "云测试"),
        cloud_developers=get_role_members(raw_members, "云开发"),
        web_developers=get_role_members(raw_members, "web前端开发"),
        app_developers=get_role_members(raw_members, "app开发"),
        ui_testers=get_role_members(raw_members, "系统测试"),
    )
