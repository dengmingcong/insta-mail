"""Core of projects with all the endpoints."""

import datetime
from typing import Annotated

import requests
from fastapi import APIRouter, Depends
from sqlmodel import select

from src.adapters.vesync.projects import constants as project_constants
from src.adapters.vesync.projects import service as project_service
from src.adapters.vesync.projects.dependencies import get_fresh_user
from src.adapters.vesync.projects.exceptions import (
    NoTasksAssignedToApiTesterFoundError,
    OrganizationNotFoundError,
    PmApiError,
)
from src.adapters.vesync.projects.models import (
    ApiTesterSummary,
    CloudDeveloperSummary,
    Organization,
    PmProject,
    PmProjectPublic,
    PmUser,
    PmUserCreate,
    PmUserPublic,
    ProjectCiTestSummary,
    ProjectMembers,
    UserOtp,
    UserPasswordAuthNeedOtpResult,
)
from src.adapters.vesync.projects.utils import (
    get_project_position_members,
    get_project_tasks_by_category_and_owner,
    get_task_filed_values,
    str_to_date,
)
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
) -> list[PmProjectPublic]:
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
        PmProjectPublic(id=project["projectId"], title=project["projectFullName"])
        for project in response.json()["result"]["projectList"]
    ]


@router.get("/{project_id}")
async def read_project(
    project_id: int,
    fresh_pm_user: Annotated[PmUser, Depends(get_fresh_user)],
    session: SessionDep,
) -> PmProject:
    """Query project details by project ID.

    :param project_id: Project ID.
    :param fresh_pm_user: The user with a fresh token.
    """
    # Call PM API to get project members.
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

    # Search for organization 'vesync' in the database.
    org = session.exec(
        select(Organization).where(Organization.name == "vesync")
    ).first()

    # If organization not found, raise error.
    if not org:
        raise OrganizationNotFoundError()

    # Call PM API to get project tasks.
    response = requests.post(
        project_constants.PM_API_ORIGIN + project_constants.API_GET_PROJECT_TASKS,
        json={
            "context": {
                **project_constants.PM_API_CONTEXT,
                "method": "getRelatedProjectTask",
                "accountID": fresh_pm_user.account_id,
                "token": fresh_pm_user.access_token,
                "traceId": int(datetime.datetime.now().timestamp()),
            },
            "data": {"projectId": project_id},
        },
    )

    # Raise error if return code is not 0.
    response_json = response.json()

    if response_json["code"] != 0:
        raise PmApiError(
            f"Error occurred when calling PM API {project_constants.API_GET_PROJECT_TASKS}: {response_json}"
        )

    all_tasks: list[dict] = response_json["result"]["taskList"]

    ci_test_tasks: list[dict] = get_project_tasks_by_category_and_owner(
        org.users, all_tasks, "云CI测试", "云测试"
    )

    if not ci_test_tasks:
        raise NoTasksAssignedToApiTesterFoundError()

    # Calculate total work hours for '云测试'.
    script_tasks: list[dict] = get_project_tasks_by_category_and_owner(
        org.users, all_tasks, "云测试脚本和用例编写", "云测试"
    )

    # Calculate based on CI test tasks.
    api_tester_summary = ApiTesterSummary(
        ci_test=ProjectCiTestSummary(
            earliest_plan_start_date=min(
                get_task_filed_values(
                    ci_test_tasks, "planStartDate", formatter=str_to_date
                )
            ),
            earliest_actual_start_date=min(
                get_task_filed_values(
                    ci_test_tasks, "actualStartDate", formatter=str_to_date
                )
            ),
            latest_plan_end_date=max(
                get_task_filed_values(
                    ci_test_tasks, "planEndDate", formatter=str_to_date
                )
            ),
            latest_actual_end_date=max(
                get_task_filed_values(
                    ci_test_tasks, "actualEndDate", formatter=str_to_date
                )
            ),
            plan_work_hours=(
                ci_test_plan := sum(
                    get_task_filed_values(ci_test_tasks, "planWorkHour")
                )
            ),
            actual_work_hours=(
                ci_test_actual := sum(
                    get_task_filed_values(ci_test_tasks, "actualWorkHour")
                )
            ),
        ),
        total_plan_work_hours=sum(get_task_filed_values(script_tasks, "planWorkHour"))
        + ci_test_plan,
        total_actual_work_hours=sum(
            get_task_filed_values(script_tasks, "actualWorkHour")
        )
        + ci_test_actual,
    )

    # Calculate work hours for '云开发'.
    cloud_developer_design_tasks: list[dict] = get_project_tasks_by_category_and_owner(
        org.users, all_tasks, "云开发方案设计", "云开发"
    )
    cloud_developer_api_dev_tasks: list[dict] = get_project_tasks_by_category_and_owner(
        org.users, all_tasks, "云接口开发", "云开发"
    )
    cloud_developer_summary = CloudDeveloperSummary(
        total_plan_work_hours=sum(
            get_task_filed_values(
                cloud_developer_design_tasks, "planWorkHour", is_ensure_has_value=False
            )
        )
        + sum(
            get_task_filed_values(
                cloud_developer_api_dev_tasks, "planWorkHour", is_ensure_has_value=False
            )
        ),
        total_actual_work_hours=sum(
            get_task_filed_values(
                cloud_developer_design_tasks,
                "actualWorkHour",
                is_ensure_has_value=False,
            )
        )
        + sum(
            get_task_filed_values(
                cloud_developer_api_dev_tasks,
                "actualWorkHour",
                is_ensure_has_value=False,
            )
        ),
    )

    return PmProject(
        members=ProjectMembers(
            project_managers=get_project_position_members(raw_members, "项目经理"),
            api_testers=get_project_position_members(raw_members, "云测试"),
            cloud_developers=get_project_position_members(raw_members, "云开发"),
            web_developers=get_project_position_members(raw_members, "web前端开发"),
            app_developers=get_project_position_members(raw_members, "app开发"),
            ui_testers=get_project_position_members(raw_members, "系统测试"),
        ),
        api_tester_summary=api_tester_summary,
        cloud_developer_summary=cloud_developer_summary,
    )
