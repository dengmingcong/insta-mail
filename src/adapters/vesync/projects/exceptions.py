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
