from datetime import datetime

from sqlmodel import Field, SQLModel


class TokenCreate(SQLModel):
    """The data model to create a token."""

    user_id: int  # Foreign key to associate with a user.
    access_token: str
    refresh_token: str
    expires_at: int  # Timestamp in seconds.


class Token(TokenCreate, table=True):
    """Model for storing access and refresh tokens."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(default_factory=datetime.now)
    last_updated: datetime | None = Field(default_factory=datetime.now)
