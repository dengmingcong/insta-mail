"""Module specific business logic."""

import json

from fastapi import HTTPException
from requests import Session


def signin_zentao(session: Session, username: str, password: str):
    """Log into Zentao.

    :param session: The requests session object.

        Cookies are stored in the session, subsequent requests will use these cookies automatically,
        no need to manually add them to each request.

    :param username: The username for login.
    :param password: The password for login.
    """
    # Get session ID.
    response = session.get(
        "https://zentao.vesync.cn/zentao/api-getSessionID.json"
    ).json()

    # Make sure response success.
    if response["status"] != "success":
        raise HTTPException(status_code=401, detail="Failed to get session ID.")

    session_id = json.loads(response["data"])["sessionID"]

    # Perform login.
    response = session.post(
        "https://zentao.vesync.cn/zentao/user-login.json",
        params={"zentaosid": session_id, "account": username, "password": password},
    ).json()

    # Make sure login success.
    if response["status"] != "success":
        raise HTTPException(status_code=401, detail="Login failed.")
