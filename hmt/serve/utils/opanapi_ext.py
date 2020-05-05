import typing
from enum import Enum


class ApiOperation(Enum):
    READ = "read"
    INSERT = "insert"
    UPSERT = "upsert"
    DELETE = "delete"
    UNKNOWN = "unknown"


def get_x(spec, field, default: typing.Any = None) -> typing.Any:
    return default if spec._x is None else spec._x.get(field, default)
