from enum import Enum

import typing
from dataclasses import dataclass
from openapi_typed import OpenAPIObject


class EndpointType(Enum):
    UPSERT = 0
    INSERT = 1
    UPDATE = 2
    DELETE = 3
    READ = 4
    UNKNOWN = 5


@dataclass
class EndpointMeta:
    type: EndpointType
    entity: str
    id_field: str


@dataclass
class Mock:
    schema: OpenAPIObject
    endpoints_meta: typing.Dict[str, EndpointMeta]

