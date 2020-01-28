from meeshkan.schemabuilder.query import build_query, update_query, SchemaQuery
from http_types import RequestBuilder
from openapi_typed import Parameter
from typing import cast
from hamcrest import *

req = RequestBuilder.from_url(
    "https://petstore.swagger.io/v1/pets?id=32&car=ferrari")


def test_build_new_query():
    query = req['query']
    schema_query = build_query(query)
    assert_that(schema_query, has_length(2))

    query_parameter = get_query_parameter("id", schema_query)

    assert_that(query_parameter, has_entry('name', 'id'))
    assert_that(query_parameter, has_entry('in', 'query'))
    assert_that(query_parameter, has_entry('required', True))

    assert_that(query_parameter, has_key("schema"))

    query_schema = query_parameter['schema']

    assert_that(query_schema, has_entry('type', 'string'))


required_query_parameter = Parameter(name='key',
                                     required=True,
                                     schema={'type': 'string'}, **{'in': 'query'})


def get_query_parameter(name: str, parameters: SchemaQuery) -> Parameter:
    matching = [param for param in parameters if param['name'] == name][0]
    return cast(Parameter, matching)


def test_update_query_should_update_required():
    query = req['query']
    updated_query = update_query(query, [required_query_parameter])
    assert_that(updated_query, has_length(3))

    updated_for_key = get_query_parameter("key", updated_query)
    assert_that(updated_for_key, has_entry('required', False))
