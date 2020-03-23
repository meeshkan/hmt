from faker import Faker
from http_types import RequestBuilder

from meeshkan.serve.mock.faker import MeeshkanDataFaker
from meeshkan.serve.mock.faker.schema_faker import MeeshkanSchemaFaker
from meeshkan.serve.mock.matcher import valid_schema
from meeshkan.serve.mock.storage import Storage


def test_faker_1():

    request = RequestBuilder.from_dict(dict(method="post",  protocol="http", path="/", host="api.com"))
    faker = MeeshkanSchemaFaker(Faker(), request, Storage())

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
    res = faker.fake_it(schema, schema, 0)
    assert valid_schema(res, schema)

def test_faker_data():

    request = RequestBuilder.from_dict(dict(method="post",  protocol="http", path="/", host="api.com"))
    faker = MeeshkanSchemaFaker(Faker(), request, None)

    schema = {
        "definitions":
            {"item": {
            "type": "object",
            "required": ["foo", "baz"],
            "properties": {
                "foo": {"type": "number"},
                "bar": {"type": "string"},
                "baz": {"type": "string"},
            }}},
        "type": "array",
        "items": {
            "$ref": "#/definitions/item",
            },
        }
    res = faker.fake_it(schema, schema, 0)
    assert valid_schema(res, schema)

def test_faker_2():

    request = RequestBuilder.from_dict(dict(method="post",  protocol="http", path="/", host="api.com"))
    faker = MeeshkanSchemaFaker(Faker(), request, None)

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
    res = faker.fake_it(schema, schema, 0)
    assert valid_schema(res, schema)


def test_faker_3():

    request = RequestBuilder.from_dict(dict(method="post",  protocol="http", path="/", host="api.com"))
    faker = MeeshkanSchemaFaker(Faker(), request, None)

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
    res = faker.fake_it(schema, schema, 0)
    assert valid_schema(res, schema)


def test_faker_4():

    request = RequestBuilder.from_dict(dict(method="post",  protocol="http", path="/", host="api.com"))
    faker = MeeshkanSchemaFaker(Faker(), request, None)

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
    res = faker.fake_it(schema, schema, 0)
    assert valid_schema(res, schema)


def test_faker_5():

    request = RequestBuilder.from_dict(dict(method="post",  protocol="http", path="/", host="api.com"))
    faker = MeeshkanSchemaFaker(Faker(), request, None)

    schema = {"type": "array"}
    res = faker.fake_it(schema, schema, 0)
    assert valid_schema(res, schema)
