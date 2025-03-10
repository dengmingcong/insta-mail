"""Module specific constants and error codes."""

from selenium.webdriver.common.by import By


class LoginPageLocators:
    USERNAME_INPUT = (By.ID, "normal_login_username")
    PASSWORD_INPUT = (By.ID, "normal_login_password")
    LOG_IN_BUTTON = (By.CSS_SELECTOR, "button.login-form-button")


class MainPageLocators:
    ACTIVE_TAB = (By.CSS_SELECTOR, ".el-menu-item.is-active")


class VesyncService:
    """VeSync service constants."""

    PM_ORIGIN: str = "https://ops.vesync.co"
    API_PATH: str = "/platform/admin/pmProject/v2/pageProjectSummaryV2"
    API_CONTEXT: dict = {
        "osInfo": "MacIntel",
        "clientInfo": "pc",
        "clientType": "pc",
        "clientVersion": "Chrome 133",
        "timeZone": "Asia/Shanghai",
        "terminalId": "PM",
        "acceptLanguage": "en",
        "method": "pageProjectSummaryV2",
        "bizSystemId": "9f9c3543-631e-4d22-8ee8-9a58bb9845b1",
    }
