import copy
from sys import path
from meeshkan.gen.generator import parameters_o
from .update_mode import UpdateMode
from functools import reduce
from dataclasses import replace
from typing import Any, List, Sequence, Iterable, AsyncIterable, cast, Tuple, Optional, Union, TypeVar, Type, Mapping
from urllib.parse import urlunsplit
from collections import defaultdict
import json

from http_types import HttpExchange as HttpExchange
from openapi_typed_2 import Info, Paths, MediaType, Header, OpenAPIObject, PathItem, Response, Operation, Parameter, Reference, Server, Responses
from typeguard import check_type  # type: ignore

from .operation import operation_from_string, new_path_item_at_operation
from ..logger import get as getLogger
from .media_types import infer_media_type_from_nonempty, build_media_type, update_media_type, MediaTypeKey, update_text_schema
from .paths import find_matching_path, RequestPathParameters
from .param import ParamBuilder
from .servers import normalize_path_if_matches
from .result import BuildResult

_DEFAULT_PATH_ITEM = {'servers': None, 'parameters': None, 'get': None, 'put': None, 'post': None, 'delete': None, 'options': None, 'head': None, 'patch': None, 'trace': None, '_ref': None, '_x': None} 

logger = getLogger(__name__)

__all__ = ['build_schema_batch', 'build_schema_online', 'update_openapi']

def build_response_content(exchange: HttpExchange, mode: UpdateMode) -> Optional[Tuple[MediaTypeKey, MediaType]]:
    """Build response content schema from exchange.

    Arguments:
        request {HttpExchange} -- Http exchange.

    Returns:
        Optional[Tuple[str, MediaType]] -- None for empty body, tuple of media-type key and media-type otherwise.
    """
    body = exchange.response.body

    if body == '':
        return None

    media_type_key = infer_media_type_from_nonempty(body)

    media_type = build_media_type(exchange, mode, type_key=media_type_key)

    return (media_type_key, media_type)


def build_response(request: HttpExchange, mode: UpdateMode) -> Response:
    """Build new response object from request response pair.

    Response reference: https://swagger.io/specification/#responseObject

    Arguments:
        request {HttpExchange} -- Request-response pair.

    Returns:
        Response -- OpenAPI response object.
    """
    # TODO Headers and links
    content_or_none = build_response_content(request, mode)

    if content_or_none is None:
        return Response(
            description="Response description",
            headers={},
            links={},
            content=None,
            _x=None
        )

    media_type_key, media_type = content_or_none
    content = {
        media_type_key: media_type
    }

    return Response(
        description="Response description",
        headers={},
        content=content,
        links={},
        _x=None
    )


def update_response(response: Response, mode: UpdateMode, exchange: HttpExchange) -> Response:
    """Update response object.

    Response reference: https://swagger.io/specification/#responseObject

    Arguments:
        response {Response} -- Existing response object.
        exchange {HttpExchange} -- Request-response pair.

    Returns:
        Response -- Updated response object.
    """
    # TODO Update headers and links
    response_body = exchange.response.body

    if response_body == '':
        # No body, do not do anything
        # TODO How to mark empty body as a possible response if non-empty responses exist
        return response

    media_type_key = infer_media_type_from_nonempty(response_body)

    ################
    ### HEADERS
    ################
    response_headers = response.headers if response.headers is not None else {}
    # TODO: accommodate array headers (currently cuts them off)
    useable_headers: Mapping[str, str] = { k: v for k,v in exchange.response.headers.items() if k not in ['content-type', 'content-length', 'Content-Type', 'Content-Length'] and isinstance(v, str)}
    new_headers = {
            **response_headers,
            **{
            k: Header(
                schema=update_text_schema(v, mode, schema=response.headers.get(k, None))) for k, v in useable_headers.items()
            }
        }

    #############
    ### CONTENT
    #############
    response_content = response.content
    if response_content is not None and media_type_key in response_content:
        # Need to update existing media type
        existing_media_type = response_content[media_type_key]
        media_type = update_media_type(
            exchange=exchange, mode=mode, type_key=media_type_key, media_type=existing_media_type)
    else:
        media_type = build_media_type(
            exchange=exchange, mode=mode, type_key=media_type_key)

    new_content: Mapping[str, MediaType] = {media_type_key: media_type}
    response_content = {**response_content, **new_content }
    return replace(response, headers=new_headers, content=response_content)


def build_operation(exchange: HttpExchange, mode: UpdateMode) -> Operation:
    """Build new operation object from request-response pair.

    Operation reference: https://swagger.io/specification/#operationObject

    Arguments:
        request {HttpExchange} -- Request-response pair

    Returns:
        Operation -- Operation object.
    """
    response = build_response(exchange, mode)
    code = str(exchange.response.statusCode)

    request_query_params = exchange.request.query
    request_header_params = exchange.request.headers
    schema_query_params = ParamBuilder('query').build(request_query_params, mode)
    schema_header_params = ParamBuilder('header').build(request_header_params, mode)

    operation = Operation(
        summary="Operation summary",
        description="Operation description",
        operationId="id",
        responses={code: response},
        parameters=[*schema_query_params, *schema_header_params])
    return operation


def update_operation(operation: Operation, request: HttpExchange, mode: UpdateMode) -> Operation:
    """Update OpenAPI operation object.

    Operation reference: https://swagger.io/specification/#operationObject

    Arguments:
        operation {Operation} -- Existing Operation object.
        request {HttpExchange} -- Request-response pair

    Returns:
        Operation -- Updated operation
    """
    responses = operation.responses  # type: Responses
    response_code = str(request.response.statusCode)
    response: Response
    if response_code in responses:
        # Response exists
        existing_response = responses[response_code]
        # TODO: why do we have this reference check?
        if not isinstance(existing_response, Reference):
            response = update_response(existing_response, mode, request)
        else:
            raise ValueError('Meeshkan is not smart enough to build responses from references yet. Coming soon!')
    else:
        response = build_response(request, mode)

    # TODO: this is not right, we need to grab the references at some point!
    existing_parameters: Sequence[Parameter] = [x for x in operation.parameters if not isinstance(x, Reference)] if operation.parameters is not None else []
    request_query_params: Mapping[str, Union[str, Sequence[str]]] = request.request.query
    request_header_params: Mapping[str, Union[str, Sequence[str]]] = request.request.headers
    _updated_parameters = [*ParamBuilder('query').update(request_query_params,
            mode, existing_parameters),
            # TODO: can we avoid the cast below? it is pretty hackish
        *ParamBuilder('header').update(request_header_params,
            mode, existing_parameters)]
    updated_parameters: List[Parameter] = []
    for i, param in enumerate(_updated_parameters):
        if len([x for x in _updated_parameters[i+1:] if (x.name == param.name) and (x._in == param._in)]) == 0:
            updated_parameters.append(param)
    new_responses: Mapping[str, Response] = { response_code: response }
    return replace(operation, responses={ **operation.responses, **new_responses }, parameters = updated_parameters)


T = TypeVar('T')


def verify_not_ref(item: Union[Reference, Any], expected_type: Type[T]) -> T:
    assert not '$ref' in item, "Did not expect a reference"
    return cast(T, item)


def update_openapi(schema: OpenAPIObject, exchange: HttpExchange, mode: UpdateMode) -> OpenAPIObject:
    """Update OpenAPI schema with a new request-response pair.
    Does not mutate the input schema.

    Schema reference: https://swagger.io/specification/#oasObject

    Returns:
        OpenAPI -- Updated schema
    """
    request_method = exchange.request.method.value
    request_path = exchange.request.pathname

    serverz = [] if schema.servers is None else schema.servers

    normalized_pathname_or_none = normalize_path_if_matches(
        exchange.request, serverz)
    if normalized_pathname_or_none is None:
        normalized_pathname = request_path
    else:
        normalized_pathname = normalized_pathname_or_none

    schema_paths = schema.paths
    operation_candidate = build_operation(exchange, mode)
    path_match_result = find_matching_path(normalized_pathname, schema_paths, request_method, operation_candidate)

    request_path_parameters = {}
    make_new_paths = True
    if path_match_result is not None:
        # Path item exists for request path
        path_item, request_path_parameters, pathname_with_wildcard, pathname_to_be_replaced_with_wildcard = path_match_result.path, path_match_result.param_mapping, path_match_result.pathname_with_wildcard, path_match_result.pathname_to_be_replaced_with_wildcard
        # Create a wildcard if the mode is not replay/mixed
        if (pathname_to_be_replaced_with_wildcard is not None):
            if mode == UpdateMode.GEN:
                # the algorithm has updated the pathname, need to mutate
                # the schema paths to use the new and discard the old if the old exists
                # in the schema. it would not exist if we have already put a wildcard
                pointer_to_value = schema_paths[pathname_to_be_replaced_with_wildcard]
                schema_paths = { k: v for k, v in [(pathname_with_wildcard, pointer_to_value), *schema_paths.items()] if k != pathname_to_be_replaced_with_wildcard }
                parameters_to_assign_to_pathname_with_wildcard = [] if schema_paths[pathname_with_wildcard].parameters is None else schema_paths[pathname_with_wildcard].parameters
                for path_param in request_path_parameters.keys():
                    params = [x for x in parameters_to_assign_to_pathname_with_wildcard if not isinstance(x, Reference)]
                    if not (path_param in [x.name for x in params if x._in == 'path']):
                        parameters_to_assign_to_pathname_with_wildcard = [Parameter(
                            required=True,
                            _in='path',
                            name=path_param,
                        ), *parameters_to_assign_to_pathname_with_wildcard]
                schema_paths = {
                    **schema_paths,
                    pathname_with_wildcard: replace(schema_paths[pathname_with_wildcard], parameters=parameters_to_assign_to_pathname_with_wildcard)
                }
                make_new_paths = False # because we've already done it above
            else:
                # we are using recordings, so we shouldn't overwrite anything
                # we only add if it is not there yet
                if normalized_pathname not in schema_paths:
                    # TODO: merge with liens below?
                    path_item = PathItem(summary="Path summary",
                             description="Path description")
                    request_path_parameters = {}
    else:
        path_item = PathItem(summary="Path summary",
                             description="Path description")
        request_path_parameters = {}
        new_paths: Paths = { normalized_pathname: path_item }
    existing_operation = operation_from_string(path_item, request_method)
    if existing_operation is not None:
        # Operation exists
        operation = update_operation(existing_operation, exchange, mode)
    else:
        operation = operation_candidate

    path_item = new_path_item_at_operation(path_item, request_method, operation)
    new_paths = { path_match_result.pathname_with_wildcard if (mode == UpdateMode.GEN) and ((path_match_result is not None) and (path_match_result.pathname_with_wildcard is not None)) else normalized_pathname: path_item } if make_new_paths else {}
    new_server = Server(url=urlunsplit(
            [str(exchange.request.protocol.value), exchange.request.host, '', '', '']))
    return replace(
        schema,
        paths={ **schema_paths, **new_paths },
        servers=serverz if (new_server.url in [x.url for x in serverz]) else [*serverz, new_server]
    )


BASE_SCHEMA = OpenAPIObject(openapi="3.0.0",
                            info=Info(title="API title",
                                      description="API description",
                                      version="1.0",
                                      termsOfService=None,
                                      contact=None,
                                      _license=None,
                                      _x=None),
                            paths={},
                            externalDocs=None,
                            servers=None,
                            security=None,
                            tags=None,
                            components=None,
                            _x=None)


async def build_schema_async(async_iter: AsyncIterable[HttpExchange],  mode: UpdateMode, starting_spec: OpenAPIObject) -> AsyncIterable[BuildResult]:
    schema = starting_spec
    async for exchange in async_iter:
        schema = update_openapi(schema, exchange, mode)
        yield BuildResult(openapi=schema)


def build_schema_online(requests: Iterable[HttpExchange], mode: UpdateMode, base_schema: OpenAPIObject = BASE_SCHEMA) -> OpenAPIObject:
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
        schema, req, mode), requests, base_schema)

    return schema


def build_schema_batch(requests: List[HttpExchange], mode: UpdateMode = UpdateMode.GEN, base_schema: OpenAPIObject = BASE_SCHEMA) -> OpenAPIObject:
    """Build OpenAPI schema from a list of request-response object.

    OpenAPI object reference: https://swagger.io/specification/#oasObject

    Arguments:
        requests {List[HttpExchange]} -- List of request-response pairs.

    Returns:
        OpenAPI -- OpenAPI object.
    """
    return build_schema_online(iter(requests), mode, base_schema=base_schema)
