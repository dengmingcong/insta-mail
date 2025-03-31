"""For pydantic models."""

from pydantic import BaseModel


class MailIn(BaseModel):
    """Pydantic model for creating a mail."""

    project_id: int
    project_name: str
    conclusion: str
    risk: str
    suggestion: str
