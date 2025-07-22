"""For pydantic models."""

from pydantic import BaseModel


class PmLoginRequest(BaseModel):
    username: str
    password: str


class PmOTPRequest(BaseModel):
    session_id: str
    otp: str


class PMProjectLocator(BaseModel):
    """Pydantic model for locating a PM project."""

    id: int
    title: str


class PMProject(BaseModel):
    """Pydantic model for PM project details."""

    project_managers: list[str]
    api_testers: list[str]
    cloud_developers: list[str]
    web_developers: list[str]
    app_developers: list[str]
    ui_testers: list[str]
