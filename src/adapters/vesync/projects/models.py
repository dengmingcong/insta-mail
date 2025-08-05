from datetime import datetime

from sqlmodel import Field, SQLModel


class PmUserBase(SQLModel):
    """Base model for user-related operations.

    :param username: Username of the user, the email part before '@'.
    """

    username: str


class PmUserCreate(PmUserBase):
    password: str


class UserPasswordAuthNeedOtpResult(SQLModel):
    """Result of user authentication with username and password that requires OTP.

    :param session_id: Session ID for OTP entry, if MFA is required.
    """

    session_id: str


class UserPasswordAuthSuccessResult(SQLModel):
    """Result of user authentication with username and password that is successful.

    :param account_id: ID in the PM system.
    :param access_token: Access token if authentication is successful.
    :param expires_at: Timestamp when the access token expires.
    """

    account_id: str
    access_token: str
    expires_at: int  # Unix timestamp in seconds


class PmUser(PmUserBase, UserPasswordAuthSuccessResult, table=True):
    """An user in PM system."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(default_factory=datetime.now)
    last_updated: datetime | None = Field(default_factory=datetime.now)


class PmUserPublic(PmUserBase):
    id: int


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
