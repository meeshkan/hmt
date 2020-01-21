import copy
from http_types import RequestResponsePair as RequestResponse
from ..logger import get as getLogger
from functools import reduce
from typing import Any, List, Iterator, cast, Tuple, Optional
from openapi_typed import Info, MediaType, OpenAPIObject, PathItem, Response, Operation, Schema
from typeguard import check_type  # type: ignore
import json
from typing_extensions import Literal
from .json_schema import to_openapi_json_schema
from .schema import validate_openapi_object

logger = getLogger(__name__)

MediaTypeKey = Literal['application/json', 'text/plain']


def get_media_type(body: str) -> Optional[MediaTypeKey]:
    """Determine media type (application/json, text/plain, etc.) from body.
    Return None for empty body.

    Arguments:
        body {str} -- Response body

    Raises:
        Exception: If body is of unexpected type.

    Returns:
        MediaTypeKey -- Media type such as "application/json"
    """

    if body == '':
        return None

    try:
        as_json = json.loads(body)
    except json.decoder.JSONDecodeError:
        logger.exception(f"Failed decoding: {body}")
        raise

    if isinstance(as_json, dict):
        return 'application/json'
    elif isinstance(as_json, list):
        return 'application/json'
    elif isinstance(as_json, str):
        return 'text/plain'
    else:
        raise Exception(f"Not sure what to do with body: {body}")


SchemaType = Literal['object', 'array', 'string']


def infer_schema(body: str, schema: Optional[Any] = None) -> Schema:
    try:
        as_json = json.loads(body)
    except json.decoder.JSONDecodeError:
        logger.exception(f"Failed decoding: {body}")
        raise

    # TODO typeguard
    return cast(Schema, to_openapi_json_schema(as_json, schema))


def update_media_type(request: RequestResponse, media_type: Optional[MediaType] = None) -> MediaType:
    body = request['res']['body']
    if media_type is not None:
        schema_or_none = media_type['schema']
    else:
        schema_or_none = None
    schema = infer_schema(body, schema=schema_or_none)
    media_type = MediaType(schema=schema)
    return media_type


def content_from_body(request: RequestResponse) -> Optional[Tuple[str, MediaType]]:
    body = request['res']['body']
    media_type_key = get_media_type(body)
    if media_type_key is None:
        return None
    media_type = update_media_type(request)
    return (media_type_key, media_type)


def build_response(request: RequestResponse) -> Response:
    """Build new response object from request response pair.

    Response reference: https://swagger.io/specification/#responseObject

    Arguments:
        request {RequestResponse} -- Request-response pair.

    Returns:
        Response -- OpenAPI response object.
    """
    # TODO Headers and links
    content_or_none = content_from_body(request)

    if content_or_none is None:
        return Response(
            description="Response description",
            headers={},
            links={}
        )

    media_type_key, media_type = content_or_none
    content = {
        media_type_key: media_type
    }

    return Response(
        description="Response description",
        headers={},
        content=content,
        links={}
    )


def update_response(response: Response, request: RequestResponse) -> Response:
    """Update response object. Mutates the input object.

    Response reference: https://swagger.io/specification/#responseObject

    Arguments:
        response {Response} -- Existing response object.
        request {RequestResponse} -- Request-response pair.

    Returns:
        Response -- Updated response object.
    """
    # TODO Update headers and links
    response_content = response['content'] if 'content' in response else None
    media_type_key = get_media_type(request['res']['body'])

    # No body
    if media_type_key is None:
        return response

    if response_content is not None and media_type_key in response_content:
        # Need to update media type
        existing_media_type = response_content[media_type_key]
        media_type = update_media_type(request, existing_media_type)
    else:
        media_type = update_media_type(request)

    response_content[media_type_key] = media_type
    return response


def build_operation(request: RequestResponse) -> Operation:
    """Build new operation object from request-response pair.

    Operation reference: https://swagger.io/specification/#operationObject

    Arguments:
        request {RequestResponse} -- Request-response pair

    Returns:
        Operation -- Operation object.
    """
    response = build_response(request)
    code = str(request['res']['statusCode'])
    operation = Operation(
        summary="Operation summary",
        description="Operation description",
        operationId="id",
        responses={code: response})
    return operation


def update_operation(operation: Operation, request: RequestResponse) -> Operation:
    """Update OpenAPI operation object. Mutates the input object.

    Operation reference: https://swagger.io/specification/#operationObject

    Arguments:
        operation {Operation} -- Existing Operation object.
        request {RequestResponse} -- Request-response pair

    Returns:
        Operation -- Updated operation
    """
    responses = operation['responses']
    response_code = str(request['res']['statusCode'])
    if response_code in responses:
        # Response exists
        existing_response = responses[response_code]
        # Ensure response is Response and not Reference
        # check_type('existing_response', existing_response, Response)
        existing_response = cast(Response, existing_response)
        response = update_response(existing_response, request)
    else:
        response = build_response(request)

    operation['responses'][response_code] = response
    return operation


def update(schema: OpenAPIObject, request: RequestResponse) -> OpenAPIObject:
    """Update OpenAPI schema with a new request-response pair.
    Does not mutate the input schema.

    Schema reference: https://swagger.io/specification/#oasObject

    Returns:
        OpenAPI -- Updated schema
    """
    schema_copy = copy.deepcopy(schema)

    method = request['req']['method']

    if request['req']['path'] in schema_copy['paths']:
        # Path item exists for request path
        path_item: PathItem = schema_copy['paths'][request['req']['path']]
    else:
        path_item = PathItem(summary="Path summary",
                             description="Path description")
        schema_copy['paths'][request['req']['path']] = path_item

    if method in path_item:
        # Operation exists
        existing_operation = path_item[method]  # type: ignore
        operation = update_operation(existing_operation, request)
    else:
        operation = build_operation(request)

    # Needs type ignore as one cannot set variable property on typed dict
    path_item[method] = operation  # type: ignore

    return cast(OpenAPIObject, schema_copy)


BASE_SCHEMA = OpenAPIObject(openapi="3.0.0",
                            info=Info(title="API title",
                                      description="API description", version="1.0"),
                            paths={})


def build_schema_online(requests: Iterator[RequestResponse]) -> OpenAPIObject:
    """Build OpenAPI schema by iterating request-response pairs.

    OpenAPI object reference: https://swagger.io/specification/#oasObject

    Arguments:
        requests {Iterator[RequestResponse]} -- Iterator of request-response pairs.

    Returns:
        OpenAPI -- OpenAPI object.
    """

    # Iterate over all request-response pairs in the iterator, starting from
    # BASE_SCHEMA
    schema = reduce(lambda schema, req: update(
        schema, req), requests, BASE_SCHEMA)

    validate_openapi_object(schema)

    return schema


def build_schema_batch(requests: List[RequestResponse]) -> OpenAPIObject:
    """Build OpenAPI schema from a list of request-response object.

    OpenAPI object reference: https://swagger.io/specification/#oasObject

    Arguments:
        requests {List[RequestResponse]} -- List of request-response pairs.

    Returns:
        OpenAPI -- OpenAPI object.
    """
    return build_schema_online(iter(requests))
