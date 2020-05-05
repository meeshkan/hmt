from typing import cast

from hamcrest import *
from http_types import RequestBuilder
from openapi_typed_2 import Parameter, Schema

from hmt.build.param import ParamBuilder, SchemaParameters
from hmt.build.update_mode import UpdateMode

req = RequestBuilder.from_url("https://petstore.swagger.io/v1/pets?id=32&car=ferrari")


def test_build_new_query():
    query = req.query
    schema_query = ParamBuilder("query").build(query, UpdateMode.GEN)
    assert_that(schema_query, has_length(2))

    query_parameter = get_query_parameter("id", schema_query)

    assert query_parameter.name == "id"
    assert query_parameter._in == "query"
    assert query_parameter.schema._type == "string"


required_query_parameter = Parameter(
    description=None,
    deprecated=None,
    allowEmptyValue=None,
    style=None,
    explode=None,
    allowReserved=None,
    content=None,
    example=None,
    examples=None,
    _x=None,
    name="key",
    required=True,
    schema=Schema(_type="string"),
    _in="query",
)


def get_query_parameter(name: str, parameters: SchemaParameters) -> Parameter:
    matching = [param for param in parameters if param.name == name][0]
    return cast(Parameter, matching)


def test_update_query_should_update_required():
    query = req.query
    updated_query = ParamBuilder("query").update(
        query, UpdateMode.GEN, [required_query_parameter]
    )
    assert_that(updated_query, has_length(3))

    updated_for_key = get_query_parameter("key", updated_query)
    assert not updated_for_key.required
