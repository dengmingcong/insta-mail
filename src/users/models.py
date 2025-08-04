from datetime import datetime

from sqlmodel import Field, SQLModel


class UserCreate(SQLModel):
    """Information required to create a user."""

    email: str
    access_token: str
    refresh_token: str
    expires_at: int  # Timestamp in seconds.


class UserUpdate(SQLModel):
    """Information required to update a user."""

    email: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    expires_at: int | None = None


class User(UserCreate, table=True):
    """Represents a user in the system."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(default_factory=datetime.now)
    last_updated: datetime | None = Field(default_factory=datetime.now)
