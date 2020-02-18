import copy
from .update_mode import UpdateMode
from functools import reduce
from typing import Any, List, Sequence, Iterable, AsyncIterable, cast, Tuple, Optional, Union, TypeVar, Type, Mapping
from urllib.parse import urlunsplit
from collections import defaultdict
import json

from http_types import HttpExchange as HttpExchange
from openapi_typed import Info, Header, MediaType, OpenAPIObject, PathItem, Response, Operation, Parameter, Reference, Server, Responses
from typeguard import check_type  # type: ignore

from ..logger import get as getLogger
from .media_types import infer_media_type_from_nonempty, build_media_type, update_media_type, MediaTypeKey, update_text_schema
from .paths import find_matching_path, RequestPathParameters
from .param import ParamBuilder
from .schema import validate_openapi_object
from .servers import normalize_path_if_matches
from .result import BuildResult


logger = getLogger(__name__)

__all__ = ['build_schema_batch', 'build_schema_online', 'update_openapi']

def build_response_content(exchange: HttpExchange, mode: UpdateMode) -> Optional[Tuple[MediaTypeKey, MediaType]]:
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


def update_response(response: Response, mode: UpdateMode, exchange: HttpExchange) -> Response:
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

    ################
    ### HEADERS
    ################
    response_headers = response.get('headers', None)
    useable_headers = {} if response_headers is None else { k: v for k,v in cast(Mapping[str, str], response_headers).items() if k not in ['content-type', 'content-length', 'Content-Type', 'Content-Length']}
    has_headers = len(useable_headers) > 0
    if response_headers is None and has_headers:
        response['headers'] = {}
    if has_headers:
        response['headers'] = {
            **response['headers'],
            **{ k: update_text_schema(v, mode, schema=response['headers'].get(k, None)) for k, v in useable_headers.items() }
        }

    #############
    ### CONTENT
    #############
    response_content = response['content'] if 'content' in response else None
    if response_content is not None and media_type_key in response_content:
        # Need to update existing media type
        existing_media_type = response_content[media_type_key]
        media_type = update_media_type(
            exchange=exchange, mode=mode, type_key=media_type_key, media_type=existing_media_type)
    else:
        media_type = build_media_type(
            exchange=exchange, mode=mode, type_key=media_type_key)

    response_content = {**response_content, **{media_type_key: media_type}}
    response['content'] = response_content
    return response


def build_operation(exchange: HttpExchange, mode: UpdateMode) -> Operation:
    """Build new operation object from request-response pair.

    Operation reference: https://swagger.io/specification/#operationObject

    Arguments:
        request {HttpExchange} -- Request-response pair

    Returns:
        Operation -- Operation object.
    """
    response = build_response(exchange, mode)
    code = str(exchange['response']['statusCode'])

    request_query_params = exchange['request'].get('query', {})
    request_header_params = exchange['request'].get('headers', {})
    schema_query_params = ParamBuilder('query').build(request_query_params, mode)
    # TODO: unfreeze
    schema_header_params = ParamBuilder('header').build(request_header_params, mode)

    operation = Operation(
        summary="Operation summary",
        description="Operation description",
        operationId="id",
        responses={code: response},
        parameters=[*schema_query_params, *schema_header_params])
    return operation


def update_operation(operation: Operation, request: HttpExchange, mode: UpdateMode) -> Operation:
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
        response = update_response(existing_response, mode, request)
    else:
        response = build_response(request, mode)

    existing_parameters = operation['parameters']
    request_query_params = request['request'].get('query', {})
    request_header_params = request['request'].get('header', {})
    ## HACK
    # because update returns a full list, we need to merge
    # we do that using json
    updated_parameters = [json.loads(y) for y in set([json.dumps(x) for x in [*ParamBuilder('query').update(request_query_params,
            mode, existing_parameters),
            # TODO: can we avoid the cast below? it is pretty hackish
        *ParamBuilder('header').update(cast(Mapping[str, Union[str, Sequence[str]]], request_header_params),
            mode, existing_parameters)]])]

    operation['parameters'] = updated_parameters
    operation['responses'][response_code] = response
    return operation


T = TypeVar('T')


def verify_not_ref(item: Union[Reference, Any], expected_type: Type[T]) -> T:
    assert not '$ref' in item, "Did not expect a reference"
    return cast(T, item)


def update_openapi(schema: OpenAPIObject, request: HttpExchange, mode: UpdateMode) -> OpenAPIObject:
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
    operation_candidate = build_operation(request, mode)
    path_match_result = find_matching_path(normalized_pathname, schema_paths, request_method, operation_candidate)

    request_path_parameters = {}

    if path_match_result is not None:
        # Path item exists for request path
        path_item, request_path_parameters, pathname_with_wildcard, pathname_to_be_replaced_with_wildcard = path_match_result['path'], path_match_result['param_mapping'], path_match_result['pathname_with_wildcard'], path_match_result['pathname_to_be_replaced_with_wildcard']
        # Create a wildcard if the mode is not replay/mixed
        if (pathname_to_be_replaced_with_wildcard is not None):
            if mode == UpdateMode.GEN:
                # the algorithm has updated the pathname, need to mutate
                # the schema paths to use the new and discard the old if the old exists
                # in the schema. it would not exist if we have already put a wildcard
                pointer_to_value = schema_paths[pathname_to_be_replaced_with_wildcard]
                schema_paths = { k: v for k, v in [(pathname_with_wildcard, pointer_to_value), *schema_paths.items()] if k != pathname_to_be_replaced_with_wildcard }
                if not ('parameters' in schema_paths[pathname_with_wildcard].keys()):
                    schema_paths[pathname_with_wildcard]['parameters'] = []
                for path_param in request_path_parameters.keys():
                    params = [cast(Parameter, x) for x in schema_paths[pathname_with_wildcard]['parameters'] if '$ref' not in x]
                    if not (path_param in [x['name'] for x in params if x['in'] == 'path']):
                        schema_paths[pathname_with_wildcard]['parameters'] = [{
                            'required': True,
                            'in': 'path',
                            'name': path_param,
                        }, *(schema_paths[pathname_with_wildcard]['parameters'])]
                schema_copy['paths'] = schema_paths
            else:
                # we are using recordings, so we shouldn't overwrite anything
                # we only add if it is not there yet
                if request_path not in schema_paths:
                    # TODO: merge with liens below?
                    path_item = PathItem(summary="Path summary",
                             description="Path description")
                    request_path_parameters = {}
                    schema_copy['paths'] = {**schema_paths, **{request_path: path_item}}
    else:
        path_item = PathItem(summary="Path summary",
                             description="Path description")
        request_path_parameters = {}
        schema_copy['paths'] = {**schema_paths, **{request_path: path_item}}
    if request_method in path_item:
        # Operation exists
        existing_operation = path_item[request_method]  # type: ignore
        operation = update_operation(existing_operation, request, mode)

    else:
        operation = operation_candidate

    # Needs type ignore as one cannot set variable property on typed dict
    path_item[request_method] = operation  # type: ignore
    return cast(OpenAPIObject, schema_copy)


BASE_SCHEMA = OpenAPIObject(openapi="3.0.0",
                            info=Info(title="API title",
                                      description="API description", version="1.0"),
                            paths={})


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

    validate_openapi_object(schema)

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
