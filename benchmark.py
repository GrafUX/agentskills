import timeit

setup = r"""
import re

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")

def _sanitize_error_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = ANSI_ESCAPE.sub("", text)
    text = "".join(c for c in text if c in "\n\r\t" or c.isprintable())
    return text

def _safe_name(name: str, max_len: int = 64) -> str:
    if not name:
        return ""
    sanitized = _sanitize_error_text(name).strip()
    sanitized = sanitized.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    if len(sanitized) > max_len:
        return sanitized[:max_len] + "..."
    return sanitized

def old_way(name):
    return _safe_name(name, max_len=100).replace("\n", " ").replace("\r", " ").replace("\t", " ")

def new_way(name):
    return _safe_name(name, max_len=100)

name = "A name with \n and \r and \t and some other things"
"""

old_time = timeit.timeit("old_way(name)", setup=setup, number=1000000)
new_time = timeit.timeit("new_way(name)", setup=setup, number=1000000)

print(f"Old time: {old_time:.4f} seconds")
print(f"New time: {new_time:.4f} seconds")
print(f"Improvement: {(old_time - new_time) / old_time * 100:.2f}%")
