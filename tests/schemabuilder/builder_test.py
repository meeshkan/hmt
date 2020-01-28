import copy

from http_types.types import HttpExchange, Request, Response
from tests.schemabuilder.paths_test import PETSTORE_SCHEMA
from meeshkan.schemabuilder import build_schema_batch, update_openapi
from meeshkan.schemabuilder.builder import BASE_SCHEMA
from meeshkan.schemabuilder.schema import validate_openapi_object
from ..util import petstore_schema, read_recordings_as_request_response
from openapi_typed import OpenAPIObject, Operation, PathItem, Response, Schema
from typeguard import check_type
import pytest
from typing import cast
from hamcrest import *
import yaml

requests = read_recordings_as_request_response()

expected_schema = copy.deepcopy(BASE_SCHEMA)

expected_schema['paths'] = {
    '/user/repos': PathItem(
        get=Operation(
            responses={
                '200': Response(description="description"),
                '403': Response(description="description")
            }
        )
    )
}

PETSTORE_SCHEMA = petstore_schema()


@pytest.fixture(scope="module")
def schema():
    return build_schema_batch(requests)


class TestSchema:
    schema = build_schema_batch(requests)

    def response_schema(self):

        return cast(Schema, self.schema['paths']['/user/repos']
                    ['get']['responses']['200']
                    ['content']['application/json']['schema'])  # type: ignore

    def test_schema_valid(self):
        validate_openapi_object(self.schema)

    def test_schema_typechecks(self):
        check_type('schema', self.schema, OpenAPIObject)

    def test_schema_keys(self):
        assert 'openapi' in self.schema
        assert 'info' in self.schema
        assert 'paths' in self.schema

    def test_paths(self):
        paths = self.schema['paths']
        assert '/user/repos' in paths

    def test_get_operation(self):
        op = self.schema['paths']['/user/repos']['get']
        assert 'responses' in op

    def test_get_operation_responses(self):
        responses = self.schema['paths']['/user/repos']['get']['responses']
        assert '200' in responses
        assert '403' in responses

    def test_200_response(self):
        response = self.schema['paths']['/user/repos']['get']['responses']['200']
        # TODO Typeguard
        response = cast(Response, response)
        assert response['headers'] == {}
        assert response['links'] == {}
        assert 'application/json' in response['content']
        media_type = response['content']['application/json']
        assert 'schema' in media_type

    def test_repos_content(self):
        content = cast(
            Response, self.schema['paths']['/user/repos']['get']['responses']['200'])['content']
        assert_that(content, has_key("application/json"))
        json_content = content['application/json']
        assert_that(json_content, has_key("schema"))
        schema = json_content['schema']
        assert_that(schema, has_entry("type", "array"))
        # TODO Typeguard for Reference
        schema = cast(Schema, schema)
        assert_that(schema, has_entry("items", instance_of(dict)))

    def test_items(self):
        schema = self.response_schema()
        items = schema['items']
        assert isinstance(items, dict)  # typeguard
        assert_that(items, has_entry('properties', instance_of(dict)))
        properties = items['properties']
        assert_that(properties, has_entry('clone_url',
                                          equal_to({'type': 'string'})))


class TestPetstoreSchemaUpdate:

    req = Request(method="get", path="/pets/32", headers={},
                  query={}, host="petstore.swagger.io", body="", protocol="https", pathname="/v1/pets/32")
    res = Response(body="", statusCode=200, headers={})
    exchange = HttpExchange(req=req, res=res)

    def test_update(self):
        updated_schema = update_openapi(PETSTORE_SCHEMA, self.exchange)
        updated_schema_paths = list(updated_schema['paths'].keys())

        assert_that(updated_schema_paths, equal_to(["/pets", "/pets/{petId}"]))

        orig_path_item = PETSTORE_SCHEMA['paths']['/pets/{petId}']
        updated_path_item = updated_schema['paths']['/pets/{petId}']

        # TODO Should builder update the path item instead of being no-op?
        assert_that(updated_path_item, equal_to(orig_path_item))


class TestQueryParameters:

    req = Request(method="get", path="/pets/32?id=1&car=ferrari", headers={},
                  query={"id": "1", "car": "ferrari"}, host="petstore.swagger.io", body="", protocol="https", pathname="/v1/pets/32")
    res = Response(body="", statusCode=200, headers={})
    exchange = HttpExchange(req=req, res=res)

    def test_update(self):
        schema = build_schema_batch([self.exchange])
        assert_that(list(schema['paths'].keys()), is_(["/pets/32"]))
