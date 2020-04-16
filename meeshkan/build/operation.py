from dataclasses import replace
from typing import Callable, Mapping

from openapi_typed_2 import Operation, Optional, PathItem


def operation_from_string(p: PathItem, s: str) -> Optional[Operation]:
    lexicon: Mapping[str, Optional[Operation]] = {
        "get": p.get,
        "post": p.post,
        "put": p.put,
        "delete": p.delete,
        "options": p.options,
        "head": p.head,
        "patch": p.patch,
        "trace": p.trace,
    }
    if s not in lexicon:
        return None
    return lexicon[s]


def new_path_item_at_operation(p: PathItem, s: str, o: Operation) -> PathItem:
    lexicon = {
        "get": {"get": o},
        "post": {"post": o},
        "put": {"put": o},
        "delete": {"delete": o},
        "options": {"options": o},
        "head": {"head": o},
        "patch": {"patch": o},
        "trace": {"trace": o},
    }
    if s not in lexicon:
        return p
    return replace(p, **lexicon[s])
