"""Module specific business logic."""

import time
from threading import Lock
from typing import Any, Dict, Union
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from playwright.sync_api import Page, expect, sync_playwright

from src.adapters.vesync.projects import constants as project_constants
from src.adapters.vesync.projects.exceptions import ValueNotFoundInLocalStorageError

router = APIRouter(prefix="/projects")

# In-memory store for Playwright sessions
_sessions: Dict[str, Dict[str, Any]] = {}
_sessions_lock = Lock()


def read_local_storage(
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


def auth_by_user_password(username: str, password: str):
    """Authenticate user with username and password using Playwright.

    :param username: Username for login.
    :param password: Password for login.
    """
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Navigate to PM login page.
    page.goto(project_constants.PM_FRONTEND_ORIGIN)

    # Input username and password.
    page.get_by_role(**project_constants.LoginPageLocators.USERNAME_INPUT).fill(
        username
    )
    page.get_by_role(**project_constants.LoginPageLocators.PASSWORD_INPUT).fill(
        password
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
        return {"status": "need_otp", "session_id": session_id}

    # Successful login, ensure navigation has fully loaded.
    page.wait_for_url("**/my-place")

    try:
        token = read_local_storage(page, "userLogin")
    except ValueNotFoundInLocalStorageError:
        raise HTTPException(
            status_code=500, detail="Timeout waiting for userLogin token."
        )

    # Close browser and playwright session before returning token.
    browser.close()
    playwright.stop()
    return {"status": "success", "token": token}
