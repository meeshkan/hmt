import copy
from typing import Optional

from genson import SchemaBuilder  # type: ignore
from openapi_typed_2 import Schema, convert_from_openapi

from .update_mode import UpdateMode


def decouple_types(s):
    if isinstance(s, dict) and "type" in s and isinstance(s["type"], list):
        return {"anyOf": [{"type": x} for x in s["type"]]}
    elif isinstance(s, dict):
        return {k: decouple_types(v) for k, v in s.items()}
    elif isinstance(s, list):
        return [decouple_types(x) for x in s]
    else:
        return s


def _to_openapi_compatible(schema):
    """OpenAPI does not strictly use JSON schema so convert to the OpenAPI subset.

    https://swagger.io/docs/specification/data-models/keywords/

    Arguments:
        schema -- Schema

    Returns:
        Modified schema
    """
    schema = copy.deepcopy(schema)
    if "$schema" in schema:
        del schema["$schema"]
    #############################
    ## genson creates array types
    ## when merging simple types
    schema = decouple_types(schema)
    return schema


def to_const(obj):
    if type(obj) == type(""):
        return {"type": "string", "enum": [obj]}
    if type(obj) == type(0):
        return {"type": "integer", "enum": [obj]}
    if type(obj) == type(0.0):
        return {"type": "number", "enum": [obj]}
    if obj is None:
        return {"type": "null"}
    if type(obj) == type(True):
        return {"type": "boolean", "enum": [obj]}
    if type(obj) == type([]):
        return {"type": "array", "items": [to_const(x) for x in obj]}
    return {
        "type": "object",
        "properties": {k: to_const(v) for k, v in obj.items()},
        "required": [x for x in obj.keys()],
    }


def to_json_schema(obj, mode: UpdateMode, schema: Optional[Schema] = None):
    """Create JSON schema based on an object.

    Arguments:
        obj {dict} -- Dictionary object

    Keyword Arguments:
        schema {dict} -- Existing schema if exists. (default: {None})

    Returns:
        [dict] -- New or updated schema.
    """
    if schema is not None:
        schema = convert_from_openapi(schema)
    if mode == UpdateMode.GEN:
        builder = SchemaBuilder()
        if schema is not None:
            builder.add_schema(schema)
        builder.add_object(obj)
        out = builder.to_schema()
        return out
    elif schema is None:
        return {"oneOf": [to_const(obj)]}
    else:
        return {"oneOf": [to_const(obj), schema]}


def to_openapi_json_schema(obj, mode: UpdateMode, schema: Optional[Schema] = None):
    """Create OpenAPI-compatible JSON schema from object.

    https://swagger.io/docs/specification/data-models/keywords/

    Arguments:
        obj {[type]} -- [description]

    Keyword Arguments:
        schema {[type]} -- [description] (default: {None})

    Returns:
        [type] -- [description]
    """
    new_schema = to_json_schema(obj, mode, schema)
    openapi_compatible_schema = _to_openapi_compatible(new_schema)
    return openapi_compatible_schema
