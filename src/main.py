"""Root of the project, which inits the FastAPI app."""

from fastapi import FastAPI

from src.projects.router import router as project_router

app = FastAPI()

app.include_router(project_router)
