from datetime import datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class PmUserBase(SQLModel):
    """Base model for user-related operations.

    :param username: Username of the user, the email part before '@'.
    """

    username: str

    @field_validator("username")
    @classmethod
    def extract_username_from_email(cls, v: str) -> str:
        """Extract username from email by removing the domain part.

        :param v: The input username or email.
        :return: Username without the email domain.
        """
        if "@" in v:
            return v.split("@")[0]
        return v


class PmUserCreate(PmUserBase):
    password: str


class UserPasswordAuthNeedOtpResult(SQLModel):
    """Result of user authentication with username and password that requires OTP.

    :param session_id: Session ID for OTP entry, if MFA is required.
    """

    session_id: str


class AuthSuccessResult(SQLModel):
    """Successful result of user authentication.

    :param account_id: ID in the PM system.
    :param access_token: Access token if authentication is successful.
    :param expires_at: Timestamp when the access token expires.
    :param all_users: All users in the PM system.
    :param organization_tree: Hierarchical structure of the organization.
    """

    account_id: str
    access_token: str
    expires_at: float  # Unix timestamp in seconds
    all_users: list[dict]
    organization_tree: dict


class PmUser(PmUserBase, AuthSuccessResult, table=True):
    """An user in PM system."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(default_factory=datetime.now)
    last_updated: datetime | None = Field(default_factory=datetime.now)


class PmUserPublic(PmUserBase):
    id: int


class UserOtp(PmUserBase):
    session_id: str
    otp: str


class PMProjectPublic(SQLModel):
    """Project information returned to the user."""

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


class Organization(SQLModel, table=True):
    """Company organization containing all users and hierarchy.

    :param id: Unique identifier for the company.
    :param name: Name of the company, in lowercase.
    :param users: All users in the company.
    :param tree: Hierarchical structure of the company.
    :param created_at: Date and time when the record was created.
    :param last_updated: Date and time when the record was last updated.
    """

    id: int = Field(default=1, primary_key=True)
    name: str = Field(default="vesync")
    users: list[dict]
    tree: dict
    created_at: datetime | None = Field(default_factory=datetime.now)
    last_updated: datetime | None = Field(default_factory=datetime.now)
