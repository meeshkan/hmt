from faker import Faker
from http_types import RequestBuilder

from meeshkan.serve.mock.faker.schema_faker import MeeshkanSchemaFaker
from meeshkan.serve.mock.matcher import valid_schema
from meeshkan.serve.mock.storage import storage_manager
from openapi_typed_2 import OpenAPIObject, PathItem, convert_to_OpenAPIObject


def get_spec(schema):
    return convert_to_OpenAPIObject({"openapi": "3.0",
                                     "info": {"title": "Title", "version": "1.1.1"},
                                     "paths": {"/":
                                                   {"get": {"responses": {"200": {"description": "some",
                                                                                  "content": {"application/json": {"schema": schema}}}}}}}})

def test_faker_1():

    request = RequestBuilder.from_dict(dict(method="get",  protocol="http", path="/", host="api.com"))

    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["foo", "baz"],
            "properties": {
                "foo": {"type": "number"},
                "bar": {"type": "string"},
                "baz": {"type": "string"},
            },
        },
    }
    res = MeeshkanSchemaFaker(Faker(), request, get_spec(schema), storage_manager.default).execute()
    assert valid_schema(res.bodyAsJson, schema)


def test_faker_2():
    request = RequestBuilder.from_dict(dict(method="get",  protocol="http", path="/", host="api.com"))

    schema = {
        "$id": "https://example.com/person.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Person",
        "type": "object",
        "properties": {
            "firstName": {"type": "string", "description": "The person's first name."},
            "lastName": {"type": "string", "description": "The person's last name."},
            "age": {
                "description": "Age in years which must be equal to or greater than zero.",
                "type": "integer",
                "minimum": 0,
            },
        },
    }
    res = MeeshkanSchemaFaker(Faker(), request, get_spec(schema), storage_manager.default).execute()
    assert valid_schema(res.bodyAsJson, schema)


def test_faker_3():

    request = RequestBuilder.from_dict(dict(method="get",  protocol="http", path="/", host="api.com"))

    schema = {
        "$id": "https://example.com/geographical-location.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Longitude and Latitude Values",
        "description": "A geographical coordinate.",
        "required": ["latitude", "longitude"],
        "type": "object",
        "properties": {
            "latitude": {"type": "number", "minimum": -90, "maximum": 90},
            "longitude": {"type": "number", "minimum": -180, "maximum": 180},
        },
    }
    res = MeeshkanSchemaFaker(Faker(), request, get_spec(schema), storage_manager.default).execute()
    assert valid_schema(res.bodyAsJson, schema)


def test_faker_4():
    request = RequestBuilder.from_dict(dict(method="get",  protocol="http", path="/", host="api.com"))

    schema = {
        "$id": "https://example.com/arrays.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "description": "A representation of a person, company, organization, or place",
        "type": "object",
        "properties": {
            "fruits": {"type": "array", "items": {"type": "string"}},
            "vegetables": {"type": "array", "items": {"$ref": "#/definitions/veggie"}},
        },
        "definitions": {
            "veggie": {
                "type": "object",
                "required": ["veggieName", "veggieLike"],
                "properties": {
                    "veggieName": {
                        "type": "string",
                        "description": "The name of the vegetable.",
                    },
                    "veggieLike": {
                        "type": "boolean",
                        "description": "Do I like this vegetable?",
                    },
                },
            }
        },
    }
    res = MeeshkanSchemaFaker(Faker(), request, get_spec(schema), storage_manager.default).execute()
    assert valid_schema(res.bodyAsJson, schema)


def test_faker_5():
    request = RequestBuilder.from_dict(dict(method="get",  protocol="http", path="/", host="api.com"))

    schema = {"type": "array"}
    res = MeeshkanSchemaFaker(Faker(), request, get_spec(schema), storage_manager.default).execute()
    assert valid_schema(res.bodyAsJson, schema)
