from datetime import datetime

from sqlmodel import Field, SQLModel


class Token(SQLModel, table=True):
    """Model for storing access and refresh tokens."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int  # Foreign key to associate with a user
    access_token: str
    refresh_token: str
    expires_at: datetime  # Expiration time for the access token
    created_at: datetime | None = Field(default_factory=datetime.now)
    last_updated: datetime | None = Field(default_factory=datetime.now)
