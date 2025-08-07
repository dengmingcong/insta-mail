"""Core of projects with all the endpoints."""

import datetime
from typing import Annotated

import requests
from fastapi import APIRouter, Depends

from src.adapters.vesync.projects import constants as project_constants
from src.adapters.vesync.projects import service as project_service
from src.adapters.vesync.projects.dependencies import get_fresh_user
from src.adapters.vesync.projects.models import (
    PMProject,
    PMProjectPublic,
    PmUser,
    PmUserCreate,
    PmUserPublic,
    UserOtp,
    UserPasswordAuthNeedOtpResult,
)
from src.adapters.vesync.projects.utils import get_role_members
from src.database import SessionDep

router = APIRouter(prefix="/projects")


@router.post("/login")
def signin_pm(
    user_in: PmUserCreate, session: SessionDep
) -> UserPasswordAuthNeedOtpResult | PmUserPublic:
    """Signin PM using Playwright.

    :param user_in: UserCreate containing username and password.
    :raises HTTPException: If login fails or MFA is required.
    """
    result = project_service.auth_by_user_password(user_in)

    # If MFA is required, return session ID for OTP entry.
    if isinstance(result, UserPasswordAuthNeedOtpResult):
        return result

    # Save authentication result to database.
    return project_service.save_auth_result_to_database(
        result, user_in.username, session
    )


@router.post("/otp")
def enter_otp(user_otp: UserOtp, session: SessionDep) -> PmUserPublic:
    """Enter OTP for MFA.

    :param user_otp: UserOtp containing username, session ID, and OTP.
    :param session: Database session for saving user.
    """
    result = project_service.enter_otp(user_otp)

    # Save authentication result to database.
    return project_service.save_auth_result_to_database(
        result, user_otp.username, session
    )


@router.get("/")
async def read_projects(
    fresh_pm_user: Annotated[PmUser, Depends(get_fresh_user)],
    title_like: str | None = None,
    page_number: int = 1,
    page_size: int = 50,
) -> list[PMProjectPublic]:
    """Query projects by matching the title.

    :param fresh_pm_user: The user with a fresh token.
    :param title_like: Title to match.
    :param page_number: Page number.
    :param page_size: Page size.
    """
    response = requests.post(
        project_constants.PM_API_ORIGIN + project_constants.API_SEARCH_PROJECTS,
        json={
            "context": {
                **project_constants.PM_API_CONTEXT,
                "method": "pageProjectSummaryV2",
                "accountID": fresh_pm_user.account_id,
                "token": fresh_pm_user.access_token,
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
        PMProjectPublic(id=project["projectId"], title=project["projectFullName"])
        for project in response.json()["result"]["projectList"]
    ]


@router.get("/{project_id}")
async def read_project(
    project_id: int,
    fresh_pm_user: Annotated[PmUser, Depends(get_fresh_user)],
) -> PMProject:
    """Query project details by project ID.

    :param project_id: Project ID.
    :param fresh_pm_user: The user with a fresh token.
    """
    response = requests.post(
        project_constants.PM_API_ORIGIN + project_constants.API_GET_PROJECT_MEMBERS,
        json={
            "context": {
                **project_constants.PM_API_CONTEXT,
                "method": "getRelatedProjectMember",
                "accountID": fresh_pm_user.account_id,
                "token": fresh_pm_user.access_token,
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
