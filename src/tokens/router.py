import datetime
import os

import requests
from fastapi import APIRouter, HTTPException
from fastapi.logger import logger
from sqlmodel import select

from src.database import SessionDep
from src.tokens.models import Token, TokenCreate
from src.utils import load_env

router = APIRouter(
    tags=["tokens"],
)

# Load environment variables
load_env()


@router.post("/tokens")
def save_token(
    token_in: TokenCreate,
    session: SessionDep,
):
    """Save access and refresh tokens."""
    token_db = Token.model_validate(token_in)

    session.add(token_db)
    session.commit()
    session.refresh(token_db)
    logger.info(f"Token saved successfully: token_id={token_db.id}")
    return {"message": "Token saved successfully", "token_id": token_db.id}


@router.patch("/tokens/{token_id}")
def refresh_access_token(
    token_id: int,
    session: SessionDep,
) -> Token:
    """Refresh access token using Microsoft's OAuth API."""
    # Query the token from the database.
    token_db = session.get(Token, token_id)

    if not token_db:
        raise HTTPException(status_code=404, detail="Token not found")

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
        "refresh_token": token_db.refresh_token,
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
    token_db.sqlmodel_update(
        {
            "access_token": response_data["access_token"],
            "refresh_token": response_data.get("refresh_token", token_db.refresh_token),
            "expires_at": datetime.datetime.now().timestamp()
            + response_data["expires_in"],
        }
    )

    session.add(token_db)
    session.commit()
    session.refresh(token_db)

    return token_db


@router.get("/tokens")
def list_tokens(session: SessionDep):
    """Retrieve a list of all tokens."""
    tokens = session.exec(select(Token)).all()
    return tokens
