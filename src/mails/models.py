"""For db models."""

from sqlmodel import Field, SQLModel


class Mail(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    project_name: str  # Type 'list' is not supported in SQLModel, a list should be converted to a string first.
    project_managers: str
    cloud_developers: str
    web_developers: str | None
    app_developers: str | None
    ui_testers: str | None
