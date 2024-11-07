"""
General utilities
"""
from typing import Any
import time
import uuid


DEBUG = True


def log_debug(message: Any, debug: bool = DEBUG) -> None:
    """
    Log a debug message if the DEBUG flag is set to True
    """
    if debug:
        print("")
        print(f"DEBUG {time.strftime('%Y-%m-%d %H:%M:%S')}: {message}")


def get_default_resultset() -> dict:
    """
    Returns a default resultset
    """
    return {
        "resultset": {},
        "error_message": "",
        "error": False,
    }


def error_resultset(
    error_message: str,
    message_code: str = ''
) -> dict:
    """
    Return an error resultset.
    """
    message_code = f" [{message_code}]" if message_code else ''
    result = get_default_resultset()
    result['error'] = True
    result['error_message'] = f"{error_message}{message_code}"
    return result


def get_date_time(timestamp: int):
    """
    Returns a formatted date and time
    """
    return time.strftime("%Y-%m-%d %H:%M:%S",
                         time.localtime(timestamp))


def get_new_item_id():
    """
    Get the new unique item id
    """
    return str(uuid.uuid4())
