"""Module specific constants and error codes."""

# PM frontend origin URL, which user input in browser.
PM_FRONTEND_ORIGIN: str = "https://pm.vesync.co/"

# PM API origin URL, which is used for API requests.
PM_API_ORIGIN: str = "https://pmapi.vesync.co"
# PM API context for requests.
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

# API paths for PM service.
API_SEARCH_PROJECTS: str = "/platform/admin/pmProject/v2/pageProjectSummaryV2"
API_GET_PROJECT_MEMBERS: str = "/platform/admin/pmProject/v2/getRelatedProjectMember"
API_GET_PROJECT_PLANS: str = "/platform/admin/pmProject/v2/getProjectSchedule"
API_GET_PROJECT_TASKS: str = "/platform/admin/pmProject/v2/getRelatedProjectTask"


class LoginPageLocators:
    USERNAME_INPUT: dict = {
        "role": "textbox",
        "name": "Please enter email prefix or email address",
    }
    PASSWORD_INPUT: dict = {"role": "textbox", "name": "Please enter password"}
    LOG_IN_BUTTON: dict = {"role": "button", "name": "Log in"}
    OTP_INPUT: dict = {
        "role": "textbox",
        "name": "Enter 6-digit code",
    }
    OTP_BUTTON: dict = {"role": "button", "name": "Verify"}


class MainPageLocators:
    TITLE: dict = {"text": "PM系统"}
