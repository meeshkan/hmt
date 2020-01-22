

from typing_extensions import TypedDict
from openapi_typed import OpenAPIObject


class BuildResult(TypedDict):
    openapi: OpenAPIObject
