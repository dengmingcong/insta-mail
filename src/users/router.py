import datetime
import os

import requests
from fastapi import APIRouter, HTTPException
from fastapi.logger import logger
from sqlmodel import select

from src.database import SessionDep
from src.users.models import User, UserCreate
from src.utils import load_env

router = APIRouter(
    tags=["users"],
    prefix="/users",
)

# Load environment variables
load_env()


@router.post("/")
def save_user(
    user_in: UserCreate,
    session: SessionDep,
):
    """Save user information."""
    user_db = User.model_validate(user_in)

    session.add(user_db)
    session.commit()
    session.refresh(user_db)
    logger.info(f"User saved successfully: user_id={user_db.id}")
    return {"message": "User saved successfully", "user_id": user_db.id}


@router.patch("/{user_id}/token")
def refresh_access_token(
    user_id: int,
    session: SessionDep,
) -> User:
    """Refresh access token using Microsoft's OAuth API."""
    # Query the user from the database.
    user_db = session.get(User, user_id)

    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")

    # Get client ID and secret from environment variables.
    client_id = os.getenv("AZURE_AD_CLIENT_ID")
    client_secret = os.getenv("AZURE_AD_CLIENT_SECRET")
    tenant_id = os.getenv("AZURE_AD_TENANT_ID")

    if not client_id or not client_secret or not tenant_id:
        raise HTTPException(
            status_code=500, detail="OAuth client credentials are not configured."
        )

    # Call Microsoft's OAuth API to refresh the access token
    oauth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": user_db.refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
    }

    response = requests.post(oauth_url, data=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to refresh access token, error: {response.text}",
        )

    response_data = response.json()

    # Update the token in the database.
    user_db.sqlmodel_update(
        {
            "access_token": response_data["access_token"],
            "refresh_token": response_data.get("refresh_token", user_db.refresh_token),
            "expires_at": datetime.datetime.now().timestamp()
            + response_data["expires_in"],
        }
    )

    session.add(user_db)
    session.commit()
    session.refresh(user_db)

    return user_db


@router.get("/")
def list_users(session: SessionDep, email: str | None = None):
    """List all users or filter by email."""
    if email:
        return session.exec(select(User).where(User.email == email)).one_or_none()

    return session.exec(select(User)).all()
