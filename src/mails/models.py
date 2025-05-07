"""For db models."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class MailBase(SQLModel):
    """Base model for mail."""

    project_name: Optional[str] = None
    conclusion: Optional[str] = None
    risk: str
    suggestion: str


class MailCreate(MailBase):
    """The data model to create a mail."""

    project_id: int


class Mail(MailBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_managers: str  # Type 'list' is not supported in SQLModel, a list should be converted to a string first.
    api_testers: str
    cloud_developers: str
    web_developers: str | None
    app_developers: str | None
    ui_testers: str | None
    created_at: datetime | None = Field(default_factory=datetime.now)
    last_updated: datetime | None = Field(default_factory=datetime.now)


class MailPublic(MailBase):
    """The public data model for mail."""

    id: int
    created_at: datetime
    last_updated: datetime


class MailPublicReadyToBeSent(SQLModel):
    """The public data model for mail ready to be sent."""

    to: list[str]
    cc: list[str]
    subject: str
    body: str
