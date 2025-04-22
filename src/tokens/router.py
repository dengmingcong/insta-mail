import os
from datetime import datetime, timedelta, timezone

import requests
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from src.database import SessionDep
from src.tokens.models import Token
from src.utils import load_env

router = APIRouter(
    tags=["tokens"],
)

# Load environment variables
load_env()


@router.post("/tokens")
def save_token(
    user_id: int,
    access_token: str,
    refresh_token: str,
    expires_in: int,
    session: SessionDep,
):
    """Save access and refresh tokens."""
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    token = Token(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )
    session.add(token)
    session.commit()
    session.refresh(token)
    return {"message": "Token saved successfully", "token_id": token.id}


@router.post("/tokens/refresh")
def refresh_access_token(
    user_id: int,
    refresh_token: str,
    session: SessionDep,
):
    """Refresh access token using Microsoft's OAuth API."""
    # Query the token from the database
    statement = select(Token).where(
        Token.user_id == user_id, Token.refresh_token == refresh_token
    )
    token = session.exec(statement).first()

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    # Get client ID and secret from environment variables
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=500, detail="OAuth client credentials are not configured"
        )

    # Call Microsoft's OAuth API to refresh the access token
    oauth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
    }

    response = requests.post(oauth_url, data=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to refresh access token"
        )

    response_data = response.json()
    new_access_token = response_data["access_token"]
    new_refresh_token = response_data.get(
        "refresh_token", refresh_token
    )  # Use the new refresh token if provided
    expires_in = response_data["expires_in"]

    # Update the token in the database
    token.access_token = new_access_token
    token.refresh_token = new_refresh_token
    token.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    token.updated_at = datetime.now(timezone.utc)

    session.add(token)
    session.commit()
    session.refresh(token)

    return {
        "message": "Access token refreshed successfully",
        "access_token": new_access_token,
        "expires_in": expires_in,
    }
