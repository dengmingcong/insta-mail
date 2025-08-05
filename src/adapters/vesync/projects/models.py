from sqlmodel import SQLModel


class UserCreate(SQLModel):
    username: str
    password: str


class PmOtpRequest(SQLModel):
    session_id: str
    otp: str


class PMProjectLocator(SQLModel):
    """Pydantic model for locating a PM project."""

    id: int
    title: str


class PMProject(SQLModel):
    """Pydantic model for PM project details."""

    project_managers: list[str]
    api_testers: list[str]
    cloud_developers: list[str]
    web_developers: list[str]
    app_developers: list[str]
    ui_testers: list[str]
