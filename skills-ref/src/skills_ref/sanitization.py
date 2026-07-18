"""Sanitization utilities for safe error message construction."""

import re

from .constants import MAX_UNTRUSTED_TEXT_LENGTH

_ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def sanitize_error_text(text: str, max_len: int = MAX_UNTRUSTED_TEXT_LENGTH) -> str:
    """Strip ANSI escape codes and truncate untrusted strings for error messages."""
    text = _ANSI_ESCAPE.sub("", text)
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def safe_name(name: str) -> str:
    """Convenience wrapper to sanitize a directory or skill name for error messages."""
    return sanitize_error_text(name, MAX_UNTRUSTED_TEXT_LENGTH)
