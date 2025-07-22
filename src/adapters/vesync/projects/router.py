"""Core of projects with all the endpoints."""

import datetime
import time
from threading import Lock
from typing import Any, Dict
from uuid import uuid4

import requests
from fastapi import APIRouter, HTTPException
from playwright.sync_api import Browser, Page, Playwright, sync_playwright
from pydantic import BaseModel

from src.adapters.vesync.projects import constants as project_constants
from src.adapters.vesync.projects import service as project_service
from src.adapters.vesync.projects.schemas import PMProject, PMProjectLocator
from src.adapters.vesync.projects.utils import get_role_members

router = APIRouter(prefix="/projects")

# In-memory store for Playwright sessions
_sessions: Dict[str, Dict[str, Any]] = {}
_sessions_lock = Lock()


class CompanyLoginRequest(BaseModel):
    username: str
    password: str


class CompanyOTPRequest(BaseModel):
    session_id: str
    otp: str


@router.post("/login")
def company_login(request: CompanyLoginRequest):
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    # Navigate to company login page
    page.goto(project_constants.VesyncService.PM_FRONTEND_ORIGIN)
    page.fill("#normal_login_username", request.username)
    page.fill("#normal_login_password", request.password)
    page.click("button.login-form-button")

    # Poll for either successful login (#app) or MFA form for 10 seconds
    max_attempts = 20
    poll_interval = 0.5

    for _ in range(max_attempts):
        try:
            # Check for successful login
            page.wait_for_selector("#app", timeout=500)
            # Login successful, poll for userLogin token
            cookies = context.cookies()
            # Poll for userLogin in localStorage
            token_attempts = 10
            token_interval = 0.5
            token = None
            for _ in range(token_attempts):
                token = page.evaluate("() => window.localStorage.getItem('userLogin')")
                if token:
                    break
                time.sleep(token_interval)
            if not token:
                browser.close()
                playwright.stop()
                raise HTTPException(
                    status_code=500, detail="Timeout waiting for userLogin token"
                )
            browser.close()
            playwright.stop()
            return {"status": "success", "cookies": cookies, "token": token}
        except Exception:
            # App element not found, check for MFA
            pass

        try:
            # Check for MFA form
            page.wait_for_selector(".mfa-form input", timeout=500)
            # MFA required
            session_id = str(uuid4())
            with _sessions_lock:
                _sessions[session_id] = {
                    "playwright": playwright,
                    "browser": browser,
                    "context": context,
                    "page": page,
                }
            return {"status": "need_otp", "session_id": session_id}
        except Exception:
            # MFA element not found, continue polling
            pass

        time.sleep(poll_interval)

    # Neither app nor MFA found after 10 seconds, login might have failed
    browser.close()
    playwright.stop()
    raise HTTPException(status_code=400, detail="Login failed or unexpected page state")


@router.post("/otp")
def company_otp(request: CompanyOTPRequest):
    with _sessions_lock:
        session = _sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    page: Page = session["page"]
    context = session["context"]
    browser: Browser = session["browser"]
    playwright: Playwright = session["playwright"]
    page.fill(".mfa-form input", request.otp)
    page.click(".mfa-form button:first-of-type")
    page.wait_for_load_state("networkidle")
    cookies = context.cookies()
    # Poll for userLogin in localStorage
    max_attempts = 10
    poll_interval = 0.5
    token = None
    for _ in range(max_attempts):
        token = page.evaluate("() => window.localStorage.getItem('userLogin')")
        if token:
            break
        time.sleep(poll_interval)
    if not token:
        browser.close()
        playwright.stop()
        raise HTTPException(
            status_code=500, detail="Timeout waiting for userLogin token"
        )
    browser.close()
    playwright.stop()
    with _sessions_lock:
        del _sessions[request.session_id]
    return {"status": "success", "cookies": cookies, "token": token}


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
