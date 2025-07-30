"""Module specific exceptions, e.g. `PostNotFound`, `InvalidUserData`."""

from src.exceptions import BaseError


class ElementNotFoundError(BaseError):
    """Raised when an element is not found."""

    pass


class ValueNotFoundInLocalStorageError(BaseError):
    """Raised when a value is not found in local storage."""

    pass
