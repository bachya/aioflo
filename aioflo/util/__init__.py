"""Define general utilities."""
from ..errors import RequestError


def raise_on_invalid_argument(value, options):
    """Raise a RequestError when an invalid consumption interval is provided."""
    if value not in options:
        raise RequestError(
            f"Invalid keyword argument: {value} (valid options: {options})"
        )
