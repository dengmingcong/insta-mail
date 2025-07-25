"""Core of projects with all the endpoints."""

import datetime
import time
from threading import Lock
from typing import Any, Dict
from uuid import uuid4

import requests
from fastapi import APIRouter, HTTPException
from playwright.sync_api import Browser, Page, Playwright, expect, sync_playwright

from src.adapters.vesync.projects import constants as project_constants
from src.adapters.vesync.projects import service as project_service
from src.adapters.vesync.projects.schemas import (
    PmLoginRequest,
    PmOtpRequest,
    PMProject,
    PMProjectLocator,
)
from src.adapters.vesync.projects.utils import get_role_members

router = APIRouter(prefix="/projects")

# In-memory store for Playwright sessions
_sessions: Dict[str, Dict[str, Any]] = {}
_sessions_lock = Lock()


@router.post("/login")
def signin_pm(request: PmLoginRequest):
    """Signin PM using Playwright.

    :param request: PmLoginRequest containing username and password.
    :raises HTTPException: If login fails or MFA is required.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Navigate to PM login page.
        page.goto(project_constants.VesyncService.PM_FRONTEND_ORIGIN)

        # Input username and password.
        page.get_by_role("textbox", name="请输入邮箱前缀或邮箱地址").fill(
            request.username
        )
        page.get_by_role("textbox", name="请输入密码").fill(request.password)
        page.get_by_role("button", name="登 录").click()

        # Wait for either successful login or MFA form.
        homepage = page.get_by_text("PM系统")
        opt_input = page.get_by_role("textbox", name="请输入6位验证码")
        expect(homepage.or_(opt_input).first).to_be_visible()

        # MFA required, return session ID for OTP entry.
        if opt_input.is_visible():
            session_id = str(uuid4())
            with _sessions_lock:
                _sessions[session_id] = {
                    "playwright": p,
                    "browser": browser,
                    "context": context,
                    "page": page,
                }
            return {"status": "need_otp", "session_id": session_id}

        # Successful login, check for 'userLogin' token in localStorage.
        TOKEN_ATTEMPTS = 10
        TOKEN_INTERVAL = 0.5
        token = None
        for _ in range(TOKEN_ATTEMPTS):
            token = page.evaluate("() => window.localStorage.getItem('userLogin')")
            if token:
                break
            time.sleep(TOKEN_INTERVAL)
        if not token:
            raise HTTPException(
                status_code=500, detail="Timeout waiting for userLogin token"
            )
        return {"status": "success", "token": token}

    # If we reach here, it means login failed or unexpected page state.
    raise HTTPException(status_code=400, detail="Login failed or unexpected page state")


@router.post("/otp")
def enter_otp(request: PmOtpRequest):
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
