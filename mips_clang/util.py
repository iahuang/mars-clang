from typing import Optional, TypeVar
import re

def with_unix_endl(string: str) -> str:
    """Return [string] with UNIX-style line endings"""

    return string.replace("\r\n", "\n").replace("\r", "")

T = TypeVar("T")


def unwrap(v: Optional[T]) -> T:
    """
    Unrwap an optional value. Raise a ValueError if the value is None.
    """
    
    if v is not None:
        return v
    raise ValueError("attempted to unwrap None value")

def ltrim(s: str, q: str) -> str:
    if not s.startswith(q):
        return s
    
    return s[len(q):]

def rtrim(s: str, q: str) -> str:
    if not s.endswith(q):
        return s
    
    return s[:-len(q)]

def ltrim_regex(s: str, pattern: str) -> Optional[tuple[str, str]]:
    match = re.match(pattern, s)
    if match:
        return (match[0], ltrim(s, match[0]))
    
    return None