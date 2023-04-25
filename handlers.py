from pathlib import Path
from typing import Any


def replace_placeholders(base_string: str, replacement_dict: dict[str, Any]) -> str:
    for name, value in replacement_dict.items():
        base_string=base_string.replace(name, str(value))
    return base_string


def generate_handler(
        handler_directory: str,
        static: dict[str, Any],
        dynamic: list[dict[str, Any]],
        repl_head: bool = False,
        repl_end: bool = False
) -> str:
    with open(Path(handler_directory) / 'base') as base_h:
        base_function = base_h.read()
    with open(Path(handler_directory) / 'head') as head_h:
        head_function = head_h.read()
    with open(Path(handler_directory) / 'end') as end_h:
        end_function = end_h.read()
    if repl_head:
        head_function = replace_placeholders(head_function, static)
    if repl_end:
        end_function = replace_placeholders(end_function, static)
    base_function = replace_placeholders(base_function, static)
    string: str = head_function + '\n'
    for dyn in dynamic:
        string += replace_placeholders(base_function, dyn) + '\n'
    string += end_function + '\n'
    return string
