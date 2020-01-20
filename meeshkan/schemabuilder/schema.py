"""OpenAPI schema validation operations.
"""

from jsonschema import validate
import json
import os
from openapi_typed import OpenAPIObject

_schema = None


def _openapi_json_schema():
    global _schema
    if _schema is not None:
        return _schema
    path = os.path.dirname(os.path.realpath(__file__))
    with open(path + "/schema.json") as f:
        _schema = json.loads(f.read())

    return _schema


def validate_openapi_object(instance: OpenAPIObject):
    return validate(instance=instance, schema=_openapi_json_schema())
