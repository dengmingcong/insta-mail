"""Non-business logic functions, e.g. response normalization, data enrichment."""

import jmespath


def get_project_role_members(project_all_members: list[dict], role: str) -> list[str]:
    """Get members by role who take part in the project.

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

    :param project_all_members: All members of all roles.
    :param role: Role to filter.
    :return: Members of the role.
    """
    members = jmespath.search(
        f"[?post.postName=='{role}'] | [0].memberList", project_all_members
    )

    return [member["userName"] for member in members] if members else []
