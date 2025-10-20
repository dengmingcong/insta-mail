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
