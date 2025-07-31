"""Root of the project, which inits the FastAPI app."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.adapters.router import router as adapter_router
from src.database import create_db_and_tables
from src.mails.router import router as mail_router
from src.users.router import router as user_router

app = FastAPI()

app.include_router(adapter_router)
app.include_router(mail_router)
app.include_router(user_router)

origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Create database and tables on startup."""
    create_db_and_tables()
