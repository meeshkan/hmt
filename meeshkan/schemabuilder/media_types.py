
"""Code for building and inferring media types (application/json, text/plain, etc.) from HTTP exchanges."""
from http_types import HttpExchange as HttpExchange
from ..logger import get as getLogger
from typing import Any, cast, Optional
from openapi_typed import MediaType, Schema
import json
from typing_extensions import Literal
from .json_schema import to_openapi_json_schema


logger = getLogger(__name__)

MediaTypeKey = Literal['application/json', 'text/plain']

MEDIA_TYPE_FOR_NON_JSON = "text/plain"


def update_json_schema(json_body: Any, schema: Optional[Any] = None) -> Schema:
    # TODO typeguard
    return cast(Schema, to_openapi_json_schema(json_body, schema))


def update_text_schema(text_body: str, schema: Optional[Any] = None) -> Schema:
    # TODO Better updates
    return {"type": "string"}


def infer_media_type_from_nonempty(body: str) -> MediaTypeKey:
    """Determine media type (application/json, text/plain, etc.) from body.

    Arguments:
        body {str} -- Response body, should not be empty.

    Raises:
        Exception: If body is of unexpected type or empty.

    Returns:
        MediaTypeKey -- Media type such as "application/json"
    """

    if body == '':
        raise Exception("Cannot infer media type from empty body.")

    try:
        as_json = json.loads(body)
    except json.decoder.JSONDecodeError:
        logger.debug(f"Failed decoding: {body}")
        # TODO Handle application/xml etc.
        return MEDIA_TYPE_FOR_NON_JSON

    if isinstance(as_json, dict) or isinstance(as_json, list):
        return 'application/json'
    elif isinstance(as_json, str):
        return 'text/plain'
    else:
        raise Exception(f"Not sure what to do with body: {body}")


def update_media_type(exchange: HttpExchange, type_key: MediaTypeKey, media_type: Optional[MediaType] = None) -> MediaType:
    """Update media type.

    Arguments:
        exchange {HttpExchange} -- Http exchange
        type_key {MediaTypeKey} -- MediaType such as "application/json"

    Keyword Arguments:
        media_type {Optional[MediaType]} -- Existing media type if exists. For example, "{ 'schema': { 'type': 'string' }}"

    Raises:
        Exception: If existing media type is unknown.

    Returns:
        MediaType -- Updated media type object.
    """
    body = exchange['response']['body']

    existing_schema = (media_type or {}).get("schema", None)

    if type_key == "application/json":
        schema = update_json_schema(json.loads(body), schema=existing_schema)
    elif type_key == "text/plain":
        schema = update_text_schema(body, schema=existing_schema)
    else:
        raise Exception("Unknown type key")
    media_type = MediaType(schema=schema)
    return media_type


def build_media_type(exchange: HttpExchange, type_key: MediaTypeKey) -> MediaType:
    return update_media_type(exchange=exchange, type_key=type_key, media_type=None)
