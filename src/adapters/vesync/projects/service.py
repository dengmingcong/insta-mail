"""Module specific business logic."""

import datetime
import json
import time
from threading import Lock
from typing import Any, Dict, Union
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from playwright.sync_api import Browser, Page, Playwright, expect, sync_playwright
from sqlmodel import Session, select

from src.adapters.vesync.projects import constants as project_constants
from src.adapters.vesync.projects.exceptions import ValueNotFoundInLocalStorageError
from src.adapters.vesync.projects.models import (
    AuthSuccessResult,
    Organization,
    PmUser,
    PmUserCreate,
    PmUserPublic,
    UserOtp,
    UserPasswordAuthNeedOtpResult,
)

router = APIRouter(prefix="/projects")

# In-memory store for Playwright sessions.
_sessions: Dict[str, Dict[str, Any]] = {}
_sessions_lock = Lock()


def _read_local_storage(
    page: Page, key: str, retry_times: int = 10, retry_interval: Union[int, float] = 0.5
) -> str:
    """Read a value from local storage with retries.

    :param page: Playwright Page object.
    :param key: The key to read from local storage.
    :param retry_times: Number of times to retry reading the value.
    :param retry_interval: Time to wait between retries in seconds.
    :return: The value from local storage.
    :raises ValueNotFoundInLocalStorageError: If the value is not found after retries.
    """
    for _ in range(retry_times):
        value = page.evaluate(f"() => window.localStorage.getItem('{key}')")
        if value:
            return value
        time.sleep(retry_interval)

    raise ValueNotFoundInLocalStorageError(
        f"Value not found in local storage for key: {key}"
    )


def auth_by_user_password(
    user_in: PmUserCreate,
) -> UserPasswordAuthNeedOtpResult | AuthSuccessResult:
    """Authenticate user with username and password using Playwright.

    :param user_in: UserCreate containing username and password.
    """
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Navigate to PM login page.
    page.goto(project_constants.PM_FRONTEND_ORIGIN)

    # Input username and password.
    page.get_by_role(**project_constants.LoginPageLocators.USERNAME_INPUT).fill(
        user_in.username
    )
    page.get_by_role(**project_constants.LoginPageLocators.PASSWORD_INPUT).fill(
        user_in.password
    )
    page.get_by_role(**project_constants.LoginPageLocators.LOG_IN_BUTTON).click()

    # Wait for either successful login or MFA form.
    homepage_title = page.get_by_text(**project_constants.MainPageLocators.TITLE)
    opt_input = page.get_by_role(**project_constants.LoginPageLocators.OTP_INPUT)
    expect(homepage_title.or_(opt_input).first).to_be_visible()

    # MFA required, return session ID for OTP entry.
    if opt_input.is_visible():
        session_id = str(uuid4())
        with _sessions_lock:
            _sessions[session_id] = {
                "playwright": playwright,
                "browser": browser,
                "context": context,
                "page": page,
            }

        # Cache session and do not close browser, waiting for OTP.
        return UserPasswordAuthNeedOtpResult(session_id=session_id)

    # Successful login, ensure navigation has fully loaded.
    page.wait_for_url("**/my-place")

    try:
        raw_token_info: str = _read_local_storage(page, "userLogin")
        token_info: dict = json.loads(raw_token_info)
        all_users: list[dict] = json.loads(_read_local_storage(page, "allAccount"))
        organization_tree: dict = json.loads(
            _read_local_storage(page, "organizationTree")
        )
    except ValueNotFoundInLocalStorageError:
        raise HTTPException(
            status_code=500, detail="Timeout waiting for userLogin token."
        )

    # Close browser and playwright session before returning token.
    browser.close()
    playwright.stop()
    return AuthSuccessResult(
        account_id=token_info["accountId"],
        access_token=token_info["token"],
        expires_at=token_info["expiredTimestamp"] / 1000,
        all_users=all_users,
        organization_tree=organization_tree,
    )


def enter_otp(otp_request: UserOtp) -> AuthSuccessResult:
    """Enter OTP for 2FA using Playwright.

    :param otp_request: PmOtpRequest containing session ID and OTP.
    :raises HTTPException: If session not found or OTP entry fails.
    """
    with _sessions_lock:
        session = _sessions.get(otp_request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    playwright: Playwright = session["playwright"]
    browser: Browser = session["browser"]
    page: Page = session["page"]

    # Fill in the OTP and submit.
    page.get_by_role(**project_constants.LoginPageLocators.OTP_INPUT).fill(
        otp_request.otp
    )
    page.get_by_role(**project_constants.LoginPageLocators.OTP_BUTTON).click()

    # Wait for successful login.
    page.wait_for_url("**/my-place")

    try:
        raw_token_info: str = _read_local_storage(page, "userLogin")
        token_info: dict = json.loads(raw_token_info)
        all_users: list[dict] = json.loads(_read_local_storage(page, "allAccount"))
        organization_tree: dict = json.loads(
            _read_local_storage(page, "organizationTree")
        )
    except ValueNotFoundInLocalStorageError:
        browser.close()
        playwright.stop()
        with _sessions_lock:
            del _sessions[otp_request.session_id]
        raise HTTPException(
            status_code=500, detail="Timeout waiting for userLogin token"
        )

    # Close browser and return token.
    browser.close()
    playwright.stop()
    with _sessions_lock:
        del _sessions[otp_request.session_id]
    return AuthSuccessResult(
        account_id=token_info["accountId"],
        access_token=token_info["token"],
        expires_at=token_info["expiredTimestamp"] / 1000,
        all_users=all_users,
        organization_tree=organization_tree,
    )


def save_auth_result_to_database(
    auth_result: AuthSuccessResult, username: str, session: Session
) -> PmUserPublic:
    """Save authentication result to database, handling both Organization and User.

    :param auth_result: The successful authentication result containing user and org data.
    :param username: Username of the authenticated user.
    :param session: Database session for saving data.
    :return: Public user information.
    """
    # Check if organization already exists in database
    org_statement = select(Organization).where(Organization.name == "vesync")
    existing_org = session.exec(org_statement).first()

    if existing_org:
        # Update existing organization with new data
        existing_org.users = auth_result.all_users
        existing_org.tree = auth_result.organization_tree
        existing_org.last_updated = datetime.datetime.now()
        session.add(existing_org)
    else:
        # Create new organization
        new_org = Organization(
            name="vesync",
            users=auth_result.all_users,
            tree=auth_result.organization_tree,
        )
        session.add(new_org)

    # Check if user already exists in database
    statement = select(PmUser).where(PmUser.username == username)
    existing_user = session.exec(statement).first()

    if existing_user:
        # Update existing user with new token info
        existing_user.account_id = auth_result.account_id
        existing_user.access_token = auth_result.access_token
        existing_user.expires_at = auth_result.expires_at
        existing_user.last_updated = datetime.datetime.now()
        session.add(existing_user)
        session.commit()
        session.refresh(existing_user)
        user_db = existing_user
    else:
        # Create new user
        user_db = PmUser(
            username=username,
            account_id=auth_result.account_id,
            access_token=auth_result.access_token,
            expires_at=auth_result.expires_at,
        )
        session.add(user_db)
        session.commit()
        session.refresh(user_db)

    return PmUserPublic(username=user_db.username, id=user_db.id)  # type: ignore
