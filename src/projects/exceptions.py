"""Module specific exceptions, e.g. `PostNotFound`, `InvalidUserData`."""

from src.exceptions import BaseError


class ElementNotFoundError(BaseError):
    """Raised when an element is not found."""

    pass


class TokenNotFoundInLocalStorageError(BaseError):
    """Raised when a token is not saved to local storage."""

    pass
