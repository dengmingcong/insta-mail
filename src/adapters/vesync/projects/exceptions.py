"""Module specific exceptions, e.g. `PostNotFound`, `InvalidUserData`."""

from fastapi import HTTPException, status

from src.exceptions import BaseError


class ElementNotFoundError(BaseError):
    """Raised when an element is not found."""

    pass


class ValueNotFoundInLocalStorageError(BaseError):
    """Raised when a value is not found in local storage."""

    pass


class NoFreshUserError(HTTPException):
    """Raised when no fresh token is available."""

    def __init__(
        self,
        detail: str = "PM authentication token expired or not found. Please login again.",
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

    pass


class OrganizationNotFoundError(HTTPException):
    """Raised when the organization is not found in the database."""

    def __init__(
        self,
        detail: str = "Organization information not found in the database. You may need to log into PM again.",
    ):
        super().__init__(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail=detail,
        )

    pass


class NoTasksAssignedToApiTesterFoundError(HTTPException):
    """Raised when no tasks are assigned to API tester."""

    def __init__(
        self,
        detail: str = "没有找到分类为“云CI测试”且责任人为云测试组成员的任务",
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

    pass


class IncompleteTasksError(HTTPException):
    """Raised when there are incomplete tasks."""

    def __init__(
        self,
        detail: str = "存在未填写完成的任务，请填写完成后再来生成测试报告",
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

    pass


class PmApiError(HTTPException):
    """Raised when PM API returns an error."""

    def __init__(
        self,
        detail: str = "调用 PM 接口时返回了错误",
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )

    pass
