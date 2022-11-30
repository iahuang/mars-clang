"""
Pretty-printing utility module
"""

import dataclasses
from typing import Any
from termcolor import colored
import numbers

COLOR_NUMERIC = "cyan"
COLOR_STRING = "green"
COLOR_BOOL = "magenta"
COLOR_NONE = "magenta"
COLOR_OBJ = "yellow"
MAX_LEN_COLLECTION = 100
def _indent(s: str, by: int) -> str:
    return "\n".join(" "*by + ln for ln in s.split("\n"))

def _as_string(obj: Any, seen_objects: set[int] = set()) -> str:
    if isinstance(obj, object) and not isinstance(obj, str) and obj is not None:
        if id(obj) in seen_objects:
            return colored("[...]", COLOR_OBJ)
        seen_objects.add(id(obj))
    
    if obj is None:
        return colored("None", COLOR_OBJ)

    if isinstance(obj, numbers.Number):
        return colored(str(obj), COLOR_NUMERIC)
    
    if isinstance(obj, str):
        return colored(repr(obj), COLOR_STRING)

    if isinstance(obj, bool):
        return colored(repr(obj), COLOR_BOOL)
    
    if isinstance(obj, list):
        elements = [_as_string(n, seen_objects) for n in obj]

        if sum(len(el) + 2 for el in elements) + 2 > MAX_LEN_COLLECTION:
            return "[\n" + _indent(",\n".join(elements), 4) + "\n]"
        return "[" + ", ".join(elements) + "]"
    
    if isinstance(obj, set):
        elements = [_as_string(n, seen_objects) for n in obj]
        if sum(len(el) + 2 for el in elements) + 2 > MAX_LEN_COLLECTION:
            return "{\n" + _indent(",\n".join(elements), 4) + "\n}"
        return "{" + ", ".join(elements) + "}"
    
    if isinstance(obj, dict):
        elements = [(_as_string(n, seen_objects), _as_string(obj[n], seen_objects)) for n in obj]
        if sum(len(el[0]) + len(el[1]) + 2 for el in elements) + 2 > MAX_LEN_COLLECTION:
            return "{\n" + _indent(",\n".join(
                el[0] + ": " + el[1]
                for el in elements
            ), 4) + "\n}"
        return "{" + ", ".join(el[0] + ": " + el[1] for el in elements) + "}"
    if dataclasses.is_dataclass(obj):
        return _as_string(dataclasses.asdict(obj), seen_objects)

    return str(obj)

def prettyprint(obj: Any) -> None:
    print(_as_string(obj))

if __name__ == "__main__":
    prettyprint([1,2,3,[4,56,2,"A"]])