from openapi_typed_2 import PathItem, Operation, Optional
from typing import Callable, Mapping

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

def set_path_item_at_operation(p: PathItem, s: str, o: Operation) -> None:
    lexicon: Mapping[str, Optional[Callable[[],None]]] = {
            "get": lambda: setattr(p, 'get', o),
            "post": lambda: setattr(p, 'post', o),
            "put": lambda: setattr(p, 'put', o),
            "delete": lambda: setattr(p, 'delete', o),
            "options": lambda: setattr(p, 'options', o),
            "head": lambda: setattr(p, 'head', o),
            "patch": lambda: setattr(p, 'patch', o),
            "trace": lambda: setattr(p, 'trace', o)
        }
    if s not in lexicon:
        return None
    return lexicon[s]()