"""For db models."""

from datetime import datetime
from typing import Optional

from sqlmodel import JSON, Column, Field, SQLModel


class MailBase(SQLModel):
    """Base model for mail."""

    project_name: str
    conclusion: Optional[str] = None
    wiki: Optional[str] = None
    risk: str
    suggestion: str
    tools: list[str] = Field(sa_column=Column(JSON))
    apis: list[dict] = Field(sa_column=Column(JSON))


class MailCreate(MailBase):
    """The data model to create a mail."""

    project_id: int


class Mail(MailBase, table=True):
    """Schema for table ``mail``."""

    id: int | None = Field(default=None, primary_key=True)
    project_managers: list[str] = Field(sa_column=Column(JSON))
    api_testers: list[str] = Field(sa_column=Column(JSON))
    cloud_developers: list[str] = Field(sa_column=Column(JSON))
    web_developers: list[str] | None = Field(sa_column=Column(JSON))
    app_developers: list[str] | None = Field(sa_column=Column(JSON))
    ui_testers: list[str] | None = Field(sa_column=Column(JSON))
    created_at: datetime | None = Field(default_factory=datetime.now)
    last_updated: datetime | None = Field(default_factory=datetime.now)


class MailPublic(SQLModel):
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
