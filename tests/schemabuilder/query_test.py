from meeshkan.schemabuilder.query import build_query, update_query
from http_types import RequestBuilder, Request
from hamcrest import *

req = RequestBuilder.from_url("https://petstore.swagger.io/v1/pets?id=32")


def test_build_query():
    query = req['query']
    schema_query = build_query(query)

    assert_that(schema_query, has_length(1))
