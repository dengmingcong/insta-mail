from datetime import datetime
from typing import Literal

from sqlmodel import Field, SQLModel


class PmUserBase(SQLModel):
    """Base model for user-related operations.

    :param username: Username of the user, the email part before '@'.
    """

    username: str


class PmUserCreate(PmUserBase):
    password: str


class PmUser(PmUserBase, table=True):
    """An user in PM system."""

    id: int | None = Field(default=None, primary_key=True)
    access_token: str
    expires_at: int  # Timestamp in seconds.
    created_at: datetime | None = Field(default_factory=datetime.now)
    last_updated: datetime | None = Field(default_factory=datetime.now)


class UserPasswordAuthResult(SQLModel):
    """Result of user authentication with username and password."""

    status: Literal["SUCCESS", "NEED_OTP"]
    session_id: str | None = None


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
