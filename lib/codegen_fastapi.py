
"""
FastAPI utilities library
"""


def headers_to_dict(headers: list[tuple[bytes, bytes]]) -> dict:
    """
    Convert a FastAPI headers object to a dictionary.
    """
    return {k.decode("latin-1"): v.decode("latin-1") for k, v in headers}
