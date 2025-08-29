import re


def canonicalize_project_name(name: str) -> str:
    """Canonicalize the project name for zentao filtering.

    >>> canonicalize_project_name("S-【2507018】PLM-公共业务-数字化项目管理平台一期--项目看板")
    '【S】【2507018】PLM-公共业务-数字化项目管理平台一期--项目看板'
    >>> canonicalize_project_name("【2507018】PLM-公共业务-数字化项目管理平台一期--项目看板")
    '【2507018】PLM-公共业务-数字化项目管理平台一期--项目看板'

    :param name: The project name to canonicalize.
    """
    # Remove the leading/trailing whitespace.
    name = name.strip()

    # If the name starts with regex pattern ``[A-Z]-{0,1}``, quote the uppercase letter with '【】'
    # and remove '-'.
    match = re.match(r"(^[A-Z]-{0,1})", name)
    if match:
        return f"【{name[0]}】{name[match.end(0) :]}"

    # Otherwise, return the original name.
    return name
