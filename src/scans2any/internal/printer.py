"""Utilities for printing highlighted terminal output."""

import logging
from typing import Any

logging.basicConfig(format="%(message)s", level=logging.INFO)


class Colors:
    """Offers aliases for coloring terminal output, using ANSI escape sequences.

    E.g. include as {Colors.OKGREEN} in python f-strings to start coloring green.
    End any coloring with {Colors.ENDC}.

    Examples
    --------
    >>> print(f"{Colors.OKGREEN}Success message!{Colors.ENDC}")
    Success message!

    """

    HEADER = "\033[95m"  # Light Magenta
    OKBLUE = "\033[94m"  # Light Blue
    OKCYAN = "\033[96m"  # Light Cyan
    OKGREEN = "\033[92m"  # Light Green
    WARNING = "\033[93m"  # Light Yellow
    FAIL = "\033[91m"  # Light Red
    DEBUG = "\033[37m"  # Light gray
    ENDC = "\033[0m"  # Reset to default
    BOLD = "\033[1m"  # Bold
    UNDERLINE = "\033[4m"  # Underline


def success(msg: Any, *, return_msg: bool = False):
    """Print colored success message to terminal
    **OR** if `return_msg` is True return as colored string.

    Returns
    -------
    >>> f"{Colors.OKGREEN}{Colors.BOLD}[ + ]{Colors.ENDC} {msg}"

    """
    msg = f"{Colors.OKGREEN}{Colors.BOLD}[ + ]{Colors.ENDC} {msg}"
    return msg if return_msg else logging.info(msg)


def info(msg: Any, *, return_msg: bool = False):
    """Print colored info message to terminal
    **OR** if `return_msg` is True return as colored string.

    Returns
    -------
    >>> f"{Colors.OKCYAN}{Colors.BOLD}[ * ]{Colors.ENDC} {msg}"

    """
    msg = f"{Colors.OKCYAN}{Colors.BOLD}[ * ]{Colors.ENDC} {msg}"
    return msg if return_msg else logging.info(msg)


def failure(msg: Any, *, return_msg: bool = False):
    """Print colored failure message to terminal
    **OR** if `return_msg` is True return as colored string.

    Returns
    -------
    >>> f"{Colors.FAIL}{Colors.BOLD}[ - ] {msg} {Colors.ENDC} "

    """
    msg = f"{Colors.FAIL}{Colors.BOLD}[ - ] {msg}{Colors.ENDC}"
    return msg if return_msg else logging.error(msg)


def error(msg: Any, *, return_msg: bool = False):
    """Print colored error message to terminal
    **OR** if `return_msg` is True return as colored string.

    Returns
    -------
    >>> f"{Colors.FAIL}{Colors.BOLD}[ X ]{Colors.ENDC} {msg}"

    """
    msg = f"{Colors.FAIL}{Colors.BOLD}[ X ]{Colors.ENDC} {msg}"
    return msg if return_msg else logging.error(msg)


def warning(msg: Any, *, return_msg: bool = False):
    """Print colored warning message to terminal
    **OR** if `return_msg` is True return as colored string.

    Returns
    -------
    >>> f"{Colors.WARNING}{Colors.BOLD}[ ! ]{Colors.ENDC} {msg}"

    """
    msg = f"{Colors.WARNING}{Colors.BOLD}[ ! ]{Colors.ENDC} {msg}"
    return msg if return_msg else logging.warning(msg)


def status(msg: Any, *, return_msg: bool = False):
    """Print colored status message to terminal
    **OR** if `return_msg` is True return as colored string.

    Returns
    -------
    >>> f"{Colors.OKBLUE}{Colors.BOLD} ~ {Colors.ENDC}{msg}"

    """
    msg = f"{Colors.OKBLUE}{Colors.BOLD}~ {Colors.ENDC}{msg}"
    # level 15 is between DEBUG and INFO
    return msg if return_msg else logging.log(level=15, msg=msg)


def section(msg: Any, *, return_msg: bool = False):
    r"""Print colored section header to terminal
    **OR** if `return_msg` is True return as colored string.

    Returns
    -------
    >>> f"\n{Colors.HEADER}{Colors.BOLD}{Colors.UNDERLINE}{msg}{Colors.ENDC}"

    """
    msg = f"\n{Colors.HEADER}{Colors.BOLD}{Colors.UNDERLINE}{msg}{Colors.ENDC}"
    return msg if return_msg else logging.log(level=25, msg=msg)


def debug(msg: Any, *, return_msg: bool = False):
    """Print colored debug message to terminal
    **OR** if `return_msg` is True return as colored string.

    Returns
    -------
    >>> f"{Colors.OKCYAN} [ DEBUG ]{Colors.ENDC} {msg}"

    """
    msg = f"{Colors.DEBUG}[ DEBUG ]{Colors.ENDC} {msg}"
    return msg if return_msg else logging.debug(msg)
