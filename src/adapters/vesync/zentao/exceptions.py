from fastapi import HTTPException


class BugOpenedBeforeTestStartError(HTTPException):
    """Raised when a bug is opened before the test start time."""

    pass


class UnrecognizedBugResolutionError(HTTPException):
    """Raised when a bug has an unrecognized resolution."""

    pass
