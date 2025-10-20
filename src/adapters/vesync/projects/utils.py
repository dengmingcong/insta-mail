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


def get_project_tasks_by_category(
    project_all_tasks: list[dict], category: str
) -> list[dict]:
    """Get tasks by category in the project.

    Example of one item in ``project_all_tasks``::

        {
            "taskId": 173130,
            "tmpTask": false,
            "taskName": "CI 测试",
            "projectId": 19806,
            "taskCategoryPath": [
            {
                "categoryId": 4,
                "categoryName": "开发阶段",
                "categoryOrder": 40
            },
            {
                "categoryId": 79,
                "categoryName": "编码开发",
                "categoryOrder": 40
            },
            {
                "categoryId": 82,
                "categoryName": "云开发",
                "categoryOrder": 30
            },
            {
                "categoryId": 85,
                "categoryName": "云CI测试",
                "categoryOrder": 30
            }
            ],
            "taskDescription": "CI 测试",
            "taskOwner": {
            "userId": "a009e7ee-b148-103a-8f95-0f7eff6a78aa",
            "userName": "raigor.deng",
            "userCnName": "邓明聪"
            },
            "planWorkHour": 12,
            "progressPercentage": 100,
            "planStartDate": "2025-10-11",
            "planEndDate": "2025-10-13",
            "actualStartDate": "2025-10-11",
            "actualEndDate": "2025-10-15",
            "actualWorkHour": 27
        }

    :param project_all_tasks: All tasks in the project.
    :param category: Category to filter.
    :return: Tasks of the category.
    """
    return jmespath.search(
        f"[?taskCategoryPath[?categoryName == '{category}']]", project_all_tasks
    )
