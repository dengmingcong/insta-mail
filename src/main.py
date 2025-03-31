"""Root of the project, which inits the FastAPI app."""

from fastapi import FastAPI

from src.database import create_db_and_tables
from src.mails.router import router as mail_router
from src.projects.router import router as project_router

app = FastAPI()

app.include_router(project_router)
app.include_router(mail_router)


@app.on_event("startup")
def on_startup():
    """Create database and tables on startup."""
    create_db_and_tables()
