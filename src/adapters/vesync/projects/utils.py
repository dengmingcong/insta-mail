"""Non-business logic functions, e.g. response normalization, data enrichment."""

import jmespath


def get_role_members(all_members: list[dict], role: str) -> list[str]:
    """Get members by role.

    :param all_members: All members of all roles.
    :param role: Role to filter.
    :return: Members of the role.
    """
    members = jmespath.search(
        f"[?post.postName=='{role}'] | [0].memberList", all_members
    )

    return [member["userName"] for member in members]
