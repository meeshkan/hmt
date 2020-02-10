import copy
from functools import reduce
from typing import Any, List, Iterable, AsyncIterable, cast, Tuple, Optional, Union, TypeVar, Type
from urllib.parse import urlunsplit
from collections import defaultdict

from http_types import HttpExchange as HttpExchange
from openapi_typed import Info, MediaType, OpenAPIObject, PathItem, Response, Operation, Parameter, Reference, Server, Responses
from typeguard import check_type  # type: ignore

from ..logger import get as getLogger
from .media_types import infer_media_type_from_nonempty, build_media_type, update_media_type, MediaTypeKey
from .paths import find_matching_path, RequestPathParameters
from .query import build_query, update_query
from .schema import validate_openapi_object
from .servers import normalize_path_if_matches
from .result import BuildResult


logger = getLogger(__name__)

__all__ = ['build_schema_batch', 'build_schema_online', 'update_openapi']


def build_response_content(exchange: HttpExchange) -> Optional[Tuple[MediaTypeKey, MediaType]]:
    """Build response content schema from exchange.

    Arguments:
        request {HttpExchange} -- Http exchange.

    Returns:
        Optional[Tuple[str, MediaType]] -- None for empty body, tuple of media-type key and media-type otherwise.
    """
    body = exchange['response']['body']

    if body == '':
        return None

    media_type_key = infer_media_type_from_nonempty(body)

    media_type = build_media_type(exchange, type_key=media_type_key)

    return (media_type_key, media_type)


def build_response(request: HttpExchange) -> Response:
    """Build new response object from request response pair.

    Response reference: https://swagger.io/specification/#responseObject

    Arguments:
        request {HttpExchange} -- Request-response pair.

    Returns:
        Response -- OpenAPI response object.
    """
    # TODO Headers and links
    content_or_none = build_response_content(request)

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


def update_response(response: Response, exchange: HttpExchange) -> Response:
    """Update response object. Mutates the input object.

    Response reference: https://swagger.io/specification/#responseObject

    Arguments:
        response {Response} -- Existing response object.
        exchange {HttpExchange} -- Request-response pair.

    Returns:
        Response -- Updated response object.
    """
    # TODO Update headers and links
    response_body = exchange['response']['body']

    if response_body == '':
        # No body, do not do anything
        # TODO How to mark empty body as a possible response if non-empty responses exist
        return response

    media_type_key = infer_media_type_from_nonempty(response_body)

    response_content = response['content'] if 'content' in response else None

    if response_content is not None and media_type_key in response_content:
        # Need to update existing media type
        existing_media_type = response_content[media_type_key]
        media_type = update_media_type(
            exchange=exchange, type_key=media_type_key, media_type=existing_media_type)
    else:
        media_type = build_media_type(
            exchange=exchange, type_key=media_type_key)

    response_content = {**response_content, **{media_type_key: media_type}}
    response['content'] = response_content
    return response


def build_operation(exchange: HttpExchange) -> Operation:
    """Build new operation object from request-response pair.

    Operation reference: https://swagger.io/specification/#operationObject

    Arguments:
        request {HttpExchange} -- Request-response pair

    Returns:
        Operation -- Operation object.
    """
    response = build_response(exchange)
    code = str(exchange['response']['statusCode'])

    request_query_params = exchange['request']['query']
    schema_query_params = build_query(request_query_params)

    operation = Operation(
        summary="Operation summary",
        description="Operation description",
        operationId="id",
        responses={code: response},
        parameters=schema_query_params)
    return operation


def update_operation(operation: Operation, request: HttpExchange) -> Operation:
    """Update OpenAPI operation object. Mutates the input object.

    Operation reference: https://swagger.io/specification/#operationObject

    Arguments:
        operation {Operation} -- Existing Operation object.
        request {HttpExchange} -- Request-response pair

    Returns:
        Operation -- Updated operation
    """
    responses = operation['responses']  # type: Responses
    response_code = str(request['response']['statusCode'])
    if response_code in responses:
        # Response exists
        existing_response = responses[response_code]
        # Ensure response is Response and not Reference
        # check_type('existing_response', existing_response, Response)
        existing_response = cast(Response, existing_response)
        response = update_response(existing_response, request)
    else:
        response = build_response(request)

    existing_parameters = operation['parameters']
    request_query_params = request['request']['query']
    updated_parameters = update_query(
        request_query_params, existing_parameters)

    operation['parameters'] = updated_parameters
    operation['responses'][response_code] = response
    return operation


T = TypeVar('T')


def verify_not_ref(item: Union[Reference, Any], expected_type: Type[T]) -> T:
    assert not '$ref' in item, "Did not expect a reference"
    return cast(T, item)


def verify_path_parameters(schema_path_parameters: List[Union[Parameter, Reference]], request_path_params: RequestPathParameters) -> None:
    """Verify that the extracted path parameters from the request match those listed in the specification.

    Arguments:
        schema_path_parameters {List[Union[Parameter, Reference]]} -- List of OpenAPI parameter objects.
        request_path_params {RequestPathParameters} -- [description]
    """
    path_params_copy = dict(**request_path_params)

    for parameter in schema_path_parameters:
        param = verify_not_ref(parameter, Parameter)
        param_in = param['in']
        if param_in != 'path':
            continue

        parameter_name = param['name']
        if not parameter_name in path_params_copy:
            raise Exception(
                "Expected to find path parameter %s in request path parameters".format(parameter_name))

        del path_params_copy[parameter_name]

    remaining_keys = path_params_copy.keys()
    if len(remaining_keys) != 0:
        raise Exception(
            "Found {} extra path parameters: {}".format(len(remaining_keys), ', '.join(list(remaining_keys))))


def update_openapi(schema: OpenAPIObject, request: HttpExchange) -> OpenAPIObject:
    """Update OpenAPI schema with a new request-response pair.
    Does not mutate the input schema.

    Schema reference: https://swagger.io/specification/#oasObject

    Returns:
        OpenAPI -- Updated schema
    """
    schema_copy = copy.deepcopy(schema)

    request_method = request['request']['method']
    request_path = request['request']['pathname']

    if not 'servers' in schema_copy:
        schema_copy['servers'] = []
    schema_servers = schema_copy['servers']

    normalized_pathname_or_none = normalize_path_if_matches(
        request['request'], schema_servers)

    if normalized_pathname_or_none is None:
        schema_copy['servers'] = [*schema_copy['servers'], Server(url=urlunsplit(
            [request['request']['protocol'], request['request']['host'], '', '', '']))]
        normalized_pathname = request_path
    else:
        normalized_pathname = normalized_pathname_or_none

    schema_paths = schema_copy['paths']

    path_match_result = find_matching_path(normalized_pathname, schema_paths)

    if path_match_result is not None:
        # Path item exists for request path
        path_item, request_path_parameters = path_match_result
    else:
        path_item = PathItem(summary="Path summary",
                             description="Path description")
        request_path_parameters = {}
        schema_copy['paths'] = {**schema_paths, **{request_path: path_item}}

    if request_method in path_item:
        # Operation exists
        existing_operation = path_item[request_method]  # type: ignore
        operation = update_operation(existing_operation, request)

    else:
        operation = build_operation(request)

    # Verify path parameters are up-to-date
    existing_path_parameters = [*path_item.get('parameters', []), *operation.get('parameters', [])]

    verify_path_parameters(existing_path_parameters, request_path_parameters)

    # Needs type ignore as one cannot set variable property on typed dict
    path_item[request_method] = operation  # type: ignore

    return cast(OpenAPIObject, schema_copy)


BASE_SCHEMA = OpenAPIObject(openapi="3.0.0",
                            info=Info(title="API title",
                                      description="API description", version="1.0"),
                            paths={})


async def build_schema_async(async_iter: AsyncIterable[HttpExchange]) -> AsyncIterable[BuildResult]:
    schema = BASE_SCHEMA
    async for exchange in async_iter:
        schema = update_openapi(schema, exchange)
        yield BuildResult(openapi=schema)


def build_schema_online(requests: Iterable[HttpExchange]) -> OpenAPIObject:
    """Build OpenAPI schema by iterating request-response pairs.

    OpenAPI object reference: https://swagger.io/specification/#oasObject

    Arguments:
        requests {Iterator[HttpExchange]} -- Iterator of request-response pairs.

    Returns:
        OpenAPI -- OpenAPI object.
    """

    # Iterate over all request-response pairs in the iterator, starting from
    # BASE_SCHEMA
    schema = reduce(lambda schema, req: update_openapi(
        schema, req), requests, BASE_SCHEMA)

    validate_openapi_object(schema)

    return schema


def build_schema_batch(requests: List[HttpExchange]) -> OpenAPIObject:
    """Build OpenAPI schema from a list of request-response object.

    OpenAPI object reference: https://swagger.io/specification/#oasObject

    Arguments:
        requests {List[HttpExchange]} -- List of request-response pairs.

    Returns:
        OpenAPI -- OpenAPI object.
    """
    return build_schema_online(iter(requests))
