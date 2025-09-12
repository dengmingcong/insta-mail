"""Module specific business logic."""

import datetime
import json
from collections import defaultdict
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from requests import Session

from src.adapters.vesync.zentao.exceptions import BugOpenedBeforeTestStartError
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

    projects = json.loads(response["data"])["products"]

    # Canonicalize the project name before filtering.
    project_name = canonicalize_project_name(project_name)

    # Filter projects by name.
    print(projects)
    filtered_projects = [p for p in projects if project_name in p["name"]]

    # Make sure one and exactly one project was found.
    if len(filtered_projects) != 1:
        raise HTTPException(
            status_code=500,
            detail=f"One and exactly one project filtered by name {project_name} should be found, but found {len(filtered_projects)}.",
        )

    return filtered_projects[0]


def get_project_bugs(session: Session, project_id: str) -> list[dict]:
    """Get all bugs for a given project ID.

    :param session: The requests session object.
    :param project_id: The ID of the project to retrieve bugs for.
    :return: A list of bugs associated with the project.
        Example::

            [
                {
                    "id": "77100",
                    "product": "1642",
                    "branch": "0",
                    "module": "9426",
                    "project": "2585",
                    "plan": "0",
                    "story": "0",
                    "storyVersion": "1",
                    "task": "0",
                    "toTask": "0",
                    "toStory": "0",
                    "title": "【UAT】【1】【云平台】【历史问题】同一天创建相同神策人群标签的任务，会出现丢失用户的情况",
                    "keywords": "",
                    "severity": "3",
                    "pri": "2",
                    "type": "code_logic_defects",
                    "os": "web_backend",
                    "browser": "chrome",
                    "hardware": "",
                    "found": "",
                    "steps": "some text",
                    "status": "closed",
                    "subStatus": "",
                    "color": "",
                    "confirmed": "1",
                    "activatedCount": "0",
                    "activatedDate": "0000-00-00 00:00:00",
                    "mailto": "",
                    "openedBy": "dorawang",
                    "openedDate": "2025-06-24 12:24:42",
                    "openedBuild": "主干",
                    "assignedTo": "closed",
                    "assignedDate": "2025-06-26 09:22:49",
                    "deadline": "0000-00-00",
                    "resolvedBy": "rogercai",
                    "resolution": "leftover_bug",
                    "resolvedBuild": "主干",
                    "resolvedDate": "2025-06-24 14:52:13",
                    "closedBy": "dorawang",
                    "closedDate": "2025-06-26 09:22:49",
                    "duplicateBug": "0",
                    "linkBug": "",
                    "case": "0",
                    "caseVersion": "0",
                    "result": "0",
                    "repo": "0",
                    "entry": "",
                    "lines": "",
                    "v1": "",
                    "v2": "",
                    "repoType": "",
                    "testtask": "0",
                    "lastEditedBy": "dorawang",
                    "lastEditedDate": "2025-06-26 09:22:49",
                    "deleted": "0",
                    "planTitle": null,
                    "needconfirm": false
                }
            ]

    :raise HTTPException: If failed to get bugs.
    """
    # 100 means total bug count.
    # 2000 means page size.
    response = session.get(
        f"https://zentao.vesync.cn/zentao/bug-browse-{project_id}-0-all-0--100-2000-1.json"
    ).json()

    # Make sure response success.
    if response["status"] != "success":
        raise HTTPException(status_code=500, detail="Failed to get bugs.")

    bugs = json.loads(response["data"])["bugs"]

    return bugs


def gen_burndown_chart(
    bugs: list[dict], test_start_datetime: datetime.datetime
) -> Optional[bytes]:
    """Generate a burndown chart for the given bugs.

    :param bugs: A list of bugs read from zentao.
    :param test_start_datetime: The datetime when the testing started.
        It should be timezone-aware and earlier than any bug's openedDate.
    :return: The PNG image bytes of the generated burndown chart.
    """
    if not (total_bugs := len(bugs)):
        return

    shanghai_tz = ZoneInfo("Asia/Shanghai")

    # Get bugs' openedDate and resolvedDate.
    # Convert naive datetime strings to timezone-aware datetime objects
    opened_dates: list[datetime.datetime] = []
    resolved_dates: list[datetime.datetime] = []

    for bug in bugs:
        if bug.get("openedDate"):
            opened_dt_naive = datetime.datetime.strptime(
                bug["openedDate"], "%Y-%m-%d %H:%M:%S"
            )
            opened_dates.append(opened_dt_naive.replace(tzinfo=shanghai_tz))

        if bug.get("resolvedDate"):
            resolved_dt_naive = datetime.datetime.strptime(
                bug["resolvedDate"], "%Y-%m-%d %H:%M:%S"
            )
            resolved_dates.append(resolved_dt_naive.replace(tzinfo=shanghai_tz))

    # Sort the dates.
    opened_dates.sort()
    resolved_dates.sort()

    # Raise error if any bug is opened before test start datetime.
    if opened_dates[0] < test_start_datetime:
        raise BugOpenedBeforeTestStartError(
            status_code=500,
            detail="Some bugs are opened before the test start datetime.",
        )

    # Discovered bugs burndown data.
    x_opened: list[datetime.datetime] = [test_start_datetime]
    y_opened: list[int] = [total_bugs]

    bugs_left_to_discover = total_bugs
    bugs_discovered_by_date: dict = defaultdict(int)
    for date in opened_dates:
        bugs_discovered_by_date[date] += 1

    sorted_discovered_dates = sorted(bugs_discovered_by_date.keys())
    for date in sorted_discovered_dates:
        bugs_left_to_discover -= bugs_discovered_by_date[date]
        x_opened.append(date)
        y_opened.append(bugs_left_to_discover)

    # Resolved bugs burndown data.
    # The date (x-axis) of the first point is the date of the first discovered bug.
    x_resolved: list[datetime.datetime] = [x_opened[1]]
    y_resolved: list[int] = [total_bugs]

    bugs_left_to_resolve = total_bugs
    bugs_resolved_by_date: dict = defaultdict(int)
    for date in resolved_dates:
        bugs_resolved_by_date[date] += 1

    sorted_resolved_dates = sorted(bugs_resolved_by_date.keys())
    for date in sorted_resolved_dates:
        bugs_left_to_resolve -= bugs_resolved_by_date[date]
        x_resolved.append(date)
        y_resolved.append(bugs_left_to_resolve)
