"""Define package errors."""


class FloError(Exception):
    """Define a base error."""

    pass


class RequestError(FloError):
    """Define an error related to invalid requests."""

    pass
