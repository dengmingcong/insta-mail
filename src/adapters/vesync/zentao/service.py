"""Module specific business logic."""

import json

from fastapi import HTTPException
from requests import Session

from src.adapters.vesync.zentao.utils import canonicalize_project_name


def signin_zentao(session: Session, username: str, password: str):
    """Log into Zentao.

    :param session: The requests session object.

        Cookies are stored in the session, subsequent requests will use these cookies automatically,
        no need to manually add them to each request.

    :param username: The username for login.
    :param password: The password for login.
    :raise HTTPException: If failed to getting session ID or logging in.
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


def get_one_project_by_name(session: Session, project_name: str) -> dict:
    """Get one and exactly one project filtering by name.

    :param session: The requests session object.
    :param project_name: The name of the project to retrieve.
    :return: The project data if found, otherwise an error.
        Example::

            {
                "id": "1755",
                "name": "【S】【2507018】PLM-公共业务-数字化项目管理平台一期--项目看板",
                "code": "2507018",
                "line": "0",
                "type": "normal",
                "status": "normal",
                "subStatus": "",
                "desc": "",
                "PO": "",
                "QD": "",
                "RD": "",
                "acl": "open",
                "whitelist": "",
                "createdBy": "pmSys",
                "createdDate": "2025-07-17 10:00:23",
                "createdVersion": "12.3.3",
                "order": "8775",
                "deleted": "0"
            }
    :raise HTTPException: If failed to get all projects or if not exactly one project was found.
    """
    # Get all projects.
    response = session.get(
        "https://zentao.vesync.cn/zentao/product-ajaxGetDropMenu-1579-qa-index-.json"
    ).json()

    # Make sure response success.
    if response["status"] != "success":
        raise HTTPException(status_code=500, detail="Failed to get projects.")

    projects = json.loads(response["data"])

    # Canonicalize the project name before filtering.
    project_name = canonicalize_project_name(project_name)

    # Filter projects by name.
    filtered_projects = [p for p in projects if project_name in p["name"]]

    # Make sure one and exactly one project was found.
    if len(filtered_projects) != 1:
        raise HTTPException(
            status_code=500,
            detail=f"One and exactly one project filtered by name {project_name} should be found, but found {len(filtered_projects)}.",
        )

    return filtered_projects[0]
