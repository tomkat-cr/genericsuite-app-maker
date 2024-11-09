"""
General utilities
"""
from typing import Any
import time
import os
import json

import uuid
import requests


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


def read_file(file_path):
    """
    Reads a file and returns its content
    """
    # If the file path begins with "http", it's a URL
    if file_path.startswith("http"):
        # If the file path begins with "https://github.com",
        # we need to replace it with "https://raw.githubusercontent.com"
        # to get the raw content
        if file_path.startswith("https://github.com"):
            file_path = file_path.replace(
                "https://github.com",
                "https://raw.githubusercontent.com")
            file_path = file_path.replace("blob/", "")
        response = requests.get(file_path)
        if response.status_code == 200:
            content = response.text
        else:
            raise ValueError(f"Error reading file: {file_path}")
    else:
        with open(file_path, 'r') as f:
            content = f.read()
    return content


def read_config_file(file_path: str):
    """
    Reads a JSON file and returns its content as a dictionary
    """
    with open(file_path, 'r') as f:
        config = json.load(f)
    return config


def get_app_config(config_file_path: str = None):
    """
    Returns the app configuration
    """
    if not config_file_path:
        config_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../config/app_config.json")
    return read_config_file(config_file_path)
