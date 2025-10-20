"""Non-business logic functions, e.g. response normalization, data enrichment."""

from typing import Union

import jmespath


def get_project_position_members(
    project_all_members: list[dict], position: str
) -> list[str]:
    """Get members by position who take part in the project.

    Example of one item in ``project_all_members``::

        {
            "post": {
                "postId": 3,
                "postOrder": 999,
                "postName": "云测试"
            },
            "memberList": [
                {
                    "userId": "a009e7ee-b148-103a-8f95-0f7eff6a78aa",
                    "userName": "raigor.deng",
                    "userCnName": "邓明聪",
                    "responsible": true
                }
            ]
        }

    :param project_all_members: All members of all positions who take part in the project.
    :param position: Position to filter.
    :return: Members of the position.
    """
    members = jmespath.search(
        f"[?post.postName=='{position}'] | [0].memberList", project_all_members
    )

    return [member["userName"] for member in members] if members else []


def get_organization_position_members(
    organization_all_members: list[dict], position: str, is_username_only: bool = True
) -> list[Union[str, dict]]:
    """Get members by position in the organization.

    Example of one item in ``organization_all_members``::

        {
            "userName": "raigor.deng",
            "itUserId": "a009e7ee-b148-103a-8f95-0f7eff6a78aa",
            "leader": false,
            "organizationId": 48,
            "organizationName": "云平台测试组",
            "postId": 3,
            "postName": "云测试",
            "accountStatus": 1,
            "loginEnabled": 1,
            "weeklyReportEnabled": 1
        }

    :param organization_all_members: All members in the organization.
    :param position: Position to filter.
    :param is_username_only: Whether to return only usernames.
    :return: Members of the position.
    """
    expression = (
        f"[?postName == '{position}'].userName"
        if is_username_only
        else f"[?postName == '{position}']"
    )

    return jmespath.search(expression, organization_all_members)
