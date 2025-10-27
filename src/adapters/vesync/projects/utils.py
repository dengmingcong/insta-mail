"""Non-business logic functions, e.g. response normalization, data enrichment."""

import datetime
from typing import Any, Callable, Generator, Optional, Union

import jmespath

from src.adapters.vesync.projects.exceptions import IncompleteTasksError


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


def get_project_tasks_by_category_and_owner(
    all_organization_members: list[dict],
    project_all_tasks: list[dict],
    category: str,
    owner_position: str,
) -> list[dict]:
    """Get tasks by category and owner position in the project.

    :param all_organization_members: All members in the organization.
    :param project_all_tasks: All tasks in the project.
    :param category: Category to filter.
    :param owner_position: Owner position to filter.
    :return: Tasks of the category and owner position.
    """
    # Get members of the owner position in the organization.
    position_members = get_organization_position_members(
        all_organization_members, owner_position, is_username_only=True
    )

    # Get tasks of the category in the project.
    category_tasks = get_project_tasks_by_category(project_all_tasks, category)

    # Filter tasks by owner position members.
    return [
        task
        for task in category_tasks
        if task["taskOwner"]["userName"] in position_members
    ]


def str_to_date(date_str: str) -> datetime.date:
    """Convert string to date.

    :param date_str: Date string.
    :return: Date object.
    """
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()


def get_task_filed_values(
    tasks: list[dict],
    field_name: str,
    is_ensure_has_value: bool = True,
    formatter: Optional[Callable] = None,
) -> Generator[Any, None, None]:
    """Get dates from tasks by date field.

    :param tasks: List of tasks.
    :param field_name: Whose value to get.
    :param is_ensure_has_value: Whether to ensure the field has value.
    :param formatter: Optional formatter to format the values.
    :return: List of dates.
    """
    for task in tasks:
        if is_ensure_has_value and not task.get(field_name):
            raise IncompleteTasksError(f"任务 {task['taskName']} 尚未填写 {field_name}")

        if formatter:
            yield formatter(task[field_name])
        else:
            yield task[field_name]
