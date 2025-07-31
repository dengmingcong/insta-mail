from datetime import datetime

from sqlmodel import Field, SQLModel


class UserCreate(SQLModel):
    """Information required to create a user."""

    email: str
    access_token: str
    refresh_token: str
    expires_at: int  # Timestamp in seconds.


class User(UserCreate, table=True):
    """Represents a user in the system."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(default_factory=datetime.now)
    last_updated: datetime | None = Field(default_factory=datetime.now)
