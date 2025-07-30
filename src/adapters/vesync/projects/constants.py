"""Module specific constants and error codes."""

from selenium.webdriver.common.by import By

PM_FRONTEND_ORIGIN: str = "https://pm.vesync.co/"
PM_API_ORIGIN: str = "https://pmapi.vesync.co"
PM_API_CONTEXT: dict = {
    "osInfo": "MacIntel",
    "clientInfo": "pc",
    "clientType": "pc",
    "clientVersion": "Chrome 133",
    "timeZone": "Asia/Shanghai",
    "terminalId": "PM",
    "acceptLanguage": "en",
    "bizSystemId": "9f9c3543-631e-4d22-8ee8-9a58bb9845b1",
    "debugMode": True,
}

API_SEARCH_PROJECTS: str = "/platform/admin/pmProject/v2/pageProjectSummaryV2"
API_GET_PROJECT_MEMBERS: str = "/platform/admin/pmProject/v2/getRelatedProjectMember"
API_GET_PROJECT_PLANS: str = "/platform/admin/pmProject/v2/getProjectSchedule"


class LoginPageLocators:
    USERNAME_INPUT = (By.ID, "normal_login_username")
    PASSWORD_INPUT = (By.ID, "normal_login_password")
    LOG_IN_BUTTON = (By.CSS_SELECTOR, "button.login-form-button")


class MainPageLocators:
    ACTIVE_TAB = (By.CSS_SELECTOR, ".el-menu-item.is-active")
