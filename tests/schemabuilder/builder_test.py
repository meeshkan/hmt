import copy
from meeshkan.schemabuilder.update_mode import UpdateMode
import json
import re
from dataclasses import replace
from http_types import HttpExchange, Request, Response, RequestBuilder, HttpExchangeBuilder
from tests.schemabuilder.paths_test import PETSTORE_SCHEMA
from meeshkan.schemabuilder import build_schema_batch, update_openapi, build_schema_online
from meeshkan.schemabuilder.builder import BASE_SCHEMA
from meeshkan.schemabuilder.update_mode import UpdateMode
from meeshkan.schemabuilder.defaults import _SCHEMA_DEFAULT
from ..util import petstore_schema, read_recordings_as_request_response, POKEAPI_RECORDINGS_PATH
from openapi_typed_2 import OpenAPIObject, Operation, PathItem, Schema, Response as _Response
from typeguard import check_type
import pytest
from hamcrest import *

requests = read_recordings_as_request_response()
pokeapi_requests = read_recordings_as_request_response(POKEAPI_RECORDINGS_PATH)

expected_schema = replace(BASE_SCHEMA, paths = {
    '/user/repos': PathItem(
        get=Operation(
            responses={
                '200': _Response(description="description"),
                '403': _Response(description="description")
            }
        )
    )
})

PETSTORE_SCHEMA = petstore_schema()

@pytest.fixture
def schema():
    return build_schema_batch(requests, UpdateMode.GEN)


def test_schema_typechecks(schema):
    check_type('schema', schema, OpenAPIObject)

def test_schema_keys(schema):
    assert schema.openapi
    assert schema.info
    assert schema.paths

def test_paths(schema):
    paths = schema.paths
    assert '/user/repos' in paths

def test_get_operation(schema):
    op = schema.paths['/user/repos'].get
    assert op.responses

def test_get_operation_responses(schema):
    responses = schema.paths['/user/repos'].get.responses
    assert '200' in responses
    assert '403' in responses

def test_200_response(schema):
    response = schema.paths['/user/repos'].get.responses['200']
    assert 'x-dns-prefetch-control' in response.headers
    assert response.links == {}
    assert 'application/json' in response.content
    media_type = response.content['application/json']
    assert media_type.schema

def test_repos_content(schema):
    content = schema.paths['/user/repos'].get.responses['200'].content
    assert_that(content, has_key("application/json"))
    json_content = content['application/json']
    assert json_content.schema
    schema = json_content.schema
    assert schema._type == "array"
    # TODO Typeguard for Reference
    assert isinstance(schema.items, Schema)

def test_items(schema):
    schema = schema.paths['/user/repos'].get.responses['200'].content['application/json'].schema
    items = schema.items
    assert isinstance(items, Schema)  # typeguard
    assert isinstance(items.properties, dict)
    properties = items.properties
    assert_that(properties, has_entry('clone_url',
                                        equal_to(Schema(**{**_SCHEMA_DEFAULT, '_type': "string"}))))

def test_servers(schema):
    servers = schema.servers
    assert 1 == len(servers)
    assert 'http://api.github.com' == servers[0].url

def test_pokeapi_schema_valid(schema):
    # this should conflate to
    # /pokemon
    # /abilities/*
    # /types/*
    # /pokemon/*
    # meaning that it should recognize wildcards
    # from all these paths
    pokeapi_schema = build_schema_batch(pokeapi_requests, UpdateMode.GEN)
    paths = pokeapi_schema.paths.keys()
    assert 4 == len(paths)
    assert_that(paths, has_item("/v2/pokemon/"))
    assert_that(paths, has_item(
        matches_regexp(r'\/v2\/pokemon\/\{[\w]+\}')))
    assert_that(paths, has_item(
        matches_regexp(r'\/v2\/type\/\{[\w]+\}')))
    assert_that(paths, has_item(
        matches_regexp(r'\/v2\/ability\/\{[\w]+\}')))

#### petstore

get_pets_req = RequestBuilder.from_url(
    "http://petstore.swagger.io/v1/pets")
get_one_pet_req = RequestBuilder.from_url(
    "http://petstore.swagger.io/v1/pets/32")

pet_res = Response(bodyAsJson=None, timestamp=None, body="", statusCode=200, headers={})

@pytest.fixture
def get_one_pet_exchange():
    return HttpExchange(request=get_one_pet_req, response=pet_res)

@pytest.fixture
def get_pets_exchange():
    return HttpExchange(request=get_pets_req, response=pet_res)

@pytest.fixture
def orig_schema_paths():
    return list(PETSTORE_SCHEMA.paths.keys())

def test_update_respects_path_parameter(get_one_pet_exchange, orig_schema_paths):
    updated_schema = update_openapi(
        PETSTORE_SCHEMA, get_one_pet_exchange, UpdateMode.GEN)
    updated_schema_paths = list(updated_schema.paths.keys())
    assert_that(updated_schema_paths, is_(orig_schema_paths))

def test_update_respects_basepath(get_pets_exchange, orig_schema_paths):
    updated_schema = update_openapi(
        PETSTORE_SCHEMA, get_pets_exchange, UpdateMode.GEN)
    updated_schema_paths = list(updated_schema.paths.keys())
    assert_that(updated_schema_paths, is_(orig_schema_paths))


#####################
#### query params

query_req = RequestBuilder.from_url(
    url="https://petstore.swagger.io/v1/pets/32?id=1&car=ferrari")
query_res = Response(body="", statusCode=200, headers={}, bodyAsJson=None, timestamp=None)

@pytest.fixture
def query_exchange():
    return HttpExchange(request=query_req, response=query_res)

req_wo_query = RequestBuilder.from_url(
    url="https://petstore.swagger.io/v1/pets/32")
res_wo_query = Response(body="", statusCode=200, headers={}, bodyAsJson=None, timestamp=None)

@pytest.fixture
def exchange_wo_query():
    return HttpExchange(request=req_wo_query, response=res_wo_query)

@pytest.fixture
def expected_path_name():
    return "/v1/pets/32"

def test_build_with_query(query_exchange, expected_path_name):
    schema = build_schema_batch([query_exchange], UpdateMode.GEN)

    assert_that(list(schema.paths.keys()),
                is_([expected_path_name]))

    operation = schema.paths[expected_path_name].get

    assert operation.parameters

    parameters = operation.parameters

    assert_that(parameters, has_length(2))

    parameter_names = [param.name for param in parameters]

    assert_that(set(parameter_names), is_(set(['id', 'car'])))

def test_schema_update_with_query(exchange_wo_query, query_exchange, expected_path_name):
    schema = build_schema_batch([exchange_wo_query], UpdateMode.GEN)

    operation = schema.paths[expected_path_name].get
    assert operation.parameters == []

    updated_schema = update_openapi(schema, query_exchange, UpdateMode.GEN)

    operation = updated_schema.paths[expected_path_name].get
    assert_that(operation.parameters, has_length(2))

    first_query_param = operation.parameters[0]

    assert not first_query_param.required


text_request = RequestBuilder.from_url("https://example.com/v1")
text_response = Response(statusCode=200, body="Hello World", headers={}, bodyAsJson=None, timestamp=None)

@pytest.fixture
def text_exchange():
    return HttpExchange(request=text_request, response=text_response)

def test_build_string_body(text_exchange):
    schema = build_schema_batch([text_exchange], UpdateMode.GEN)
    response_content = schema.paths['/v1'].get.responses['200'].content

    assert_that(response_content, has_key("text/plain"))

    media_type = response_content["text/plain"]

    assert media_type.schema._type == "string"

def test_schema_in_replay_mode():
    reqs = []
    with open('tests/server/mock/callbacks/opbank/recordings/recording.jsonl','r') as rr: 
        reqs = rr.read().split('\n')

    reqs = [HttpExchangeBuilder.from_dict(json.loads(r)) for r in reqs if r != '']
    r = build_schema_batch(reqs, UpdateMode.REPLAY)
    # this schema has four recordings, of which two correspond to /v1/payments/confirm
    assert 2 == len(r.paths['/v1/payments/confirm'].post.responses['201'].content['application/json'].schema.oneOf)

import time
ACCEPTABLE_TIME = 10 # 10 seconds
def test_builder_speed():
    now = time.time()
    with open('resources/large.jsonl', 'r') as recordings:
        http_exchanges = [HttpExchangeBuilder.from_dict(json.loads(d)) for d in recordings.read().split('\n') if d != '']
        build_schema_online(iter(http_exchanges), mode=UpdateMode.REPLAY)
    assert (time.time() - now) < ACCEPTABLE_TIME