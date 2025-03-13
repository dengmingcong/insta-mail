"""For pydantic models."""

from pydantic import BaseModel


class PMProjectLocator(BaseModel):
    """Pydantic model for locating a PM project."""

    id: int
    title: str
