"""For pydantic models."""

from pydantic import BaseModel


class PMProject(BaseModel):
    """Pydantic model for PM project."""

    id: int
    name: str
