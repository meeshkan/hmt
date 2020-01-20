import copy
from genson import SchemaBuilder  # type: ignore


def _to_openapi_compatible(schema):
    """OpenAPI does not strictly use JSON schema so convert to the OpenAPI subset.

    https://swagger.io/docs/specification/data-models/keywords/

    Arguments:
        schema -- Schema

    Returns:
        Modified schema
    """
    schema = copy.deepcopy(schema)
    del schema['$schema']
    return schema


def to_json_schema(obj, schema=None):
    """Create JSON schema based on an object.

    Arguments:
        obj {dict} -- Dictionary object

    Keyword Arguments:
        schema {dict} -- Existing schema if exists. (default: {None})

    Returns:
        [dict] -- New or updated schema.
    """
    builder = SchemaBuilder()
    if schema is not None:
        builder.add_schema(schema)
    builder.add_object(obj)
    schema = builder.to_schema()
    return schema


def to_openapi_json_schema(obj, schema=None):
    """Create OpenAPI-compatible JSON schema from object.

    https://swagger.io/docs/specification/data-models/keywords/

    Arguments:
        obj {[type]} -- [description]

    Keyword Arguments:
        schema {[type]} -- [description] (default: {None})

    Returns:
        [type] -- [description]
    """
    schema = to_json_schema(obj, schema)
    openapi_compatible_schema = _to_openapi_compatible(schema)
    return openapi_compatible_schema
