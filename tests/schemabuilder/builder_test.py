import copy
from meeshkan.schemabuilder.update_mode import UpdateMode
import json
import re
from http_types import HttpExchange, Request, Response, RequestBuilder, HttpExchangeBuilder
from tests.schemabuilder.paths_test import PETSTORE_SCHEMA
from meeshkan.schemabuilder import build_schema_batch, update_openapi
from meeshkan.schemabuilder.builder import BASE_SCHEMA
from meeshkan.schemabuilder.defaults import _SCHEMA_DEFAULT
from ..util import petstore_schema, read_recordings_as_request_response, POKEAPI_RECORDINGS_PATH
from openapi_typed_2 import OpenAPIObject, Operation, PathItem, Schema, Response as _Response
from typeguard import check_type
import pytest
from hamcrest import *

requests = read_recordings_as_request_response()
pokeapi_requests = read_recordings_as_request_response(POKEAPI_RECORDINGS_PATH)

expected_schema = copy.deepcopy(BASE_SCHEMA)

_RESPONSE_DEFAULT={'headers': None, 'content':None, 'links': None, '_x':None}

expected_schema.paths = {
    '/user/repos': PathItem(
        summary=None,
        description=None,
        servers=None,
        parameters=None,
        put=None,
        post=None,
        delete=None,
        options=None,
        head=None,
        patch=None,
        trace=None,
        _ref=None,
        _x=None,
        get=Operation(
            tags=None,
            summary=None,
            description=None,
            externalDocs=None,
            operationId=None,
            parameters=None,
            callbacks=None,
            deprecated=None,
            security=None,
            servers=None,
            requestBody=None,
            _x=None,
            responses={
                '200': _Response(**{**_RESPONSE_DEFAULT, 'description': "description"}),
                '403': _Response(**{**_RESPONSE_DEFAULT, 'description': "description"})
            }
        )
    )
}

PETSTORE_SCHEMA = petstore_schema()


class TestSchema:
    schema = build_schema_batch(requests, UpdateMode.GEN)
    pokeapi_schema = build_schema_batch(pokeapi_requests, UpdateMode.GEN)

    def response_schema(self):

        return self.schema.paths['/user/repos'].get.responses['200'].content['application/json'].schema

    def test_schema_typechecks(self):
        check_type('schema', self.schema, OpenAPIObject)

    def test_schema_keys(self):
        assert self.schema.openapi
        assert self.schema.info
        assert self.schema.paths

    def test_paths(self):
        paths = self.schema.paths
        assert '/user/repos' in paths

    def test_get_operation(self):
        op = self.schema.paths['/user/repos'].get
        assert op.responses

    def test_get_operation_responses(self):
        responses = self.schema.paths['/user/repos'].get.responses
        assert '200' in responses
        assert '403' in responses

    def test_200_response(self):
        response = self.schema.paths['/user/repos'].get.responses['200']
        assert 'x-dns-prefetch-control' in response.headers
        assert response.links == {}
        assert 'application/json' in response.content
        media_type = response.content['application/json']
        assert media_type.schema

    def test_repos_content(self):
        content = self.schema.paths['/user/repos'].get.responses['200'].content
        assert_that(content, has_key("application/json"))
        json_content = content['application/json']
        assert json_content.schema
        schema = json_content.schema
        assert schema._type == "array"
        # TODO Typeguard for Reference
        assert isinstance(schema.items, Schema)

    def test_items(self):
        schema = self.response_schema()
        items = schema.items
        assert isinstance(items, Schema)  # typeguard
        assert isinstance(items.properties, dict)
        properties = items.properties
        assert_that(properties, has_entry('clone_url',
                                          equal_to(Schema(**{**_SCHEMA_DEFAULT, '_type': "string"}))))

    def test_servers(self):
        servers = self.schema.servers
        assert 1 == len(servers)
        assert 'http://api.github.com' == servers[0].url

    def test_pokeapi_schema_valid(self):
        # this should conflate to
        # /pokemon
        # /abilities/*
        # /types/*
        # /pokemon/*
        # meaning that it should recognize wildcards
        # from all these paths
        paths = self.pokeapi_schema.paths.keys()
        assert 4 == len(paths)
        assert_that(paths, has_item("/v2/pokemon/"))
        assert_that(paths, has_item(
            matches_regexp(r'\/v2\/pokemon\/\{[\w]+\}')))
        assert_that(paths, has_item(
            matches_regexp(r'\/v2\/type\/\{[\w]+\}')))
        assert_that(paths, has_item(
            matches_regexp(r'\/v2\/ability\/\{[\w]+\}')))


class TestPetstoreSchemaUpdate:

    get_pets_req = RequestBuilder.from_url(
        "http://petstore.swagger.io/v1/pets")
    get_one_pet_req = RequestBuilder.from_url(
        "http://petstore.swagger.io/v1/pets/32")

    res = Response(bodyAsJson=None, timestamp=None, body="", statusCode=200, headers={})

    get_one_pet_exchange = HttpExchange(request=get_one_pet_req, response=res)
    get_pets_exchange = HttpExchange(request=get_pets_req, response=res)

    orig_schema_paths = list(PETSTORE_SCHEMA.paths.keys())

    def test_update_respects_path_parameter(self):
        updated_schema = update_openapi(
            PETSTORE_SCHEMA, self.get_one_pet_exchange, UpdateMode.GEN)
        updated_schema_paths = list(updated_schema.paths.keys())
        assert_that(updated_schema_paths, is_(self.orig_schema_paths))

    def test_update_respects_basepath(self):
        updated_schema = update_openapi(
            PETSTORE_SCHEMA, self.get_pets_exchange, UpdateMode.GEN)
        updated_schema_paths = list(updated_schema.paths.keys())
        assert_that(updated_schema_paths, is_(self.orig_schema_paths))


class TestQueryParameters:

    req = RequestBuilder.from_url(
        url="https://petstore.swagger.io/v1/pets/32?id=1&car=ferrari")
    res = Response(body="", statusCode=200, headers={}, bodyAsJson=None, timestamp=None)
    exchange = HttpExchange(request=req, response=res)

    req_wo_query = RequestBuilder.from_url(
        url="https://petstore.swagger.io/v1/pets/32")
    res = Response(body="", statusCode=200, headers={}, bodyAsJson=None, timestamp=None)
    exchange_wo_query = HttpExchange(request=req_wo_query, response=res)

    expected_path_name = "/v1/pets/32"

    def test_build_with_query(self):
        schema = build_schema_batch([self.exchange], UpdateMode.GEN)

        assert_that(list(schema.paths.keys()),
                    is_([self.expected_path_name]))

        operation = schema.paths[self.expected_path_name].get

        assert operation.parameters

        parameters = operation.parameters

        assert_that(parameters, has_length(2))

        parameter_names = [param.name for param in parameters]

        assert_that(set(parameter_names), is_(set(['id', 'car'])))

    def test_schema_update_with_query(self):
        schema = build_schema_batch([self.exchange_wo_query], UpdateMode.GEN)

        operation = schema.paths[self.expected_path_name].get
        assert operation.parameters == []

        updated_schema = update_openapi(schema, self.exchange, UpdateMode.GEN)

        operation = updated_schema.paths[self.expected_path_name].get
        assert_that(operation.parameters, has_length(2))

        first_query_param = operation.parameters[0]

        assert not first_query_param.required


class TestSchemaTextBody:
    request = RequestBuilder.from_url("https://example.com/v1")
    response = Response(statusCode=200, body="Hello World", headers={}, bodyAsJson=None, timestamp=None)
    exchange: HttpExchange = HttpExchange(request=request, response=response)

    def test_build_string_body(self):
        schema = build_schema_batch([self.exchange], UpdateMode.GEN)
        response_content = schema.paths['/v1'].get.responses['200'].content

        assert_that(response_content, has_key("text/plain"))

        media_type = response_content["text/plain"]

        assert media_type.schema._type == "string"

class TestShemaInReplayMode:

    def test_schema_in_replay_mode(self):
        reqs = []
        with open('tests/server/mock/callbacks/opbank/recordings/recording.jsonl','r') as rr: 
            reqs = rr.read().split('\n')

        reqs = [HttpExchangeBuilder.from_dict(json.loads(r)) for r in reqs if r != '']
        r = build_schema_batch(reqs, UpdateMode.REPLAY)
        # this schema has four recordings, of which two correspond to /v1/payments/confirm
        assert 2 == len(r.paths['/v1/payments/confirm'].post.responses['201'].content['application/json'].schema.oneOf)