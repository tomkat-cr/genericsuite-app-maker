"""
General utilities
"""
from typing import Any
import time
import os
import json

import uuid
import requests


DEBUG = False


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


def read_file(file_path, params: dict = None):
    """
    Reads a file and returns its content.
    If the file_path is a URL, it will be downloaded
    If the file_path is a local file, it will be read
    if params.get("save_file") is True, it will be saved in the output_dir
    and return file_path will enclosed by [] to indicate the saved file path
    (e.g. [./output/file_name.txt])
    """
    if not params:
        params = {}
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

    # Save the file if requested by the "save_file" parameter
    # and return the file path enclosed by []
    if params.get("save_file"):
        # "./output" is the default output directory if the output_dir
        # parameter is not provided
        output_dir = params.get("output_dir", "./output")
        if params.get("file_name"):
            file_name = params.get("file_name")
        else:
            file_name = os.path.basename(file_path)
        target_file_path = save_file(output_dir, file_name, content)
        return f"[{target_file_path}]"
    return content


def is_an_url(element_url_or_path: str):
    """ Returns True if the string is an URL"""
    return element_url_or_path.startswith(
        ("http://", "https://", "ftp://", "file://")
    )


def path_exists(file_path: str):
    """
    Creates the output directory if it doesn't exist
    """
    if is_an_url(file_path):
        return None
    return os.path.exists(file_path)


def create_dirs(output_dir: str):
    """
    Creates the output directory if it doesn't exist
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


def save_file(output_dir: str, file_name: str, content: Any):
    """
    Saves the file to the output directory
    """
    # If the output_dir path does not exist, create it
    create_dirs(output_dir)
    target_file_path = f"{output_dir}/{file_name}"
    log_debug(f"READ_FILE | Saving file: {target_file_path}", debug=DEBUG)
    with open(target_file_path, 'w') as f:
        f.write(content)
        f.close()
    return target_file_path


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
