from http_types import RequestBuilder

from meeshkan.serve.mock.faker.stateful_faker import StatefulFaker
from meeshkan.serve.mock.matcher import valid_schema
from meeshkan.serve.mock.specs import OpenAPISpecification
from tests.util import spec

def test_faker_data(mock_data_store):
    faker = StatefulFaker(mock_data_store)

    request = RequestBuilder.from_dict(
        dict(method="get", protocol="http", path="/", host="api.com")
    )

    schema = {"type": "array", "items": {"$ref": "#/components/schemas/item"}}

    components = {
        "schemas": {
            "item": {
                "type": "object",
                "required": ["foo", "baz"],
                "properties": {
                    "foo": {"type": "number"},
                    "bar": {"type": "string"},
                    "baz": {"type": "string"},
                },
            }
        }
    }

    res = faker.process(
        OpenAPISpecification(
            source="default", api=spec(response_schema=schema, components=components)
        ),
        request,
    )

    schema["components"] = components
    assert valid_schema(res.bodyAsJson, schema)
    assert 0 == len(schema)

    

def test_sateless_faker_1(mock_data_store):
    faker = StatefulFaker(mock_data_store)

    request = RequestBuilder.from_dict(
        dict(method="get", protocol="http", path="/", host="api.com")
    )

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
    res = faker.process(
        OpenAPISpecification(source="default", api=spec(response_schema=schema)),
        request,
    )

    assert valid_schema(res.bodyAsJson, schema)


def test_sateless_faker_2(mock_data_store):
    faker = StatefulFaker(mock_data_store)

    request = RequestBuilder.from_dict(
        dict(method="get", protocol="http", path="/", host="api.com")
    )

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
                "minimum": 0.0,
            },
        },
    }
    res = faker.process(
        OpenAPISpecification(source="default", api=spec(response_schema=schema)),
        request,
    )

    assert valid_schema(res.bodyAsJson, schema)


def test_sateless_faker_3(mock_data_store):
    faker = StatefulFaker(mock_data_store)

    request = RequestBuilder.from_dict(
        dict(method="get", protocol="http", path="/", host="api.com")
    )

    schema = {
        "$id": "https://example.com/geographical-location.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Longitude and Latitude Values",
        "description": "A geographical coordinate.",
        "required": ["latitude", "longitude"],
        "type": "object",
        "properties": {
            "latitude": {"type": "number", "minimum": -90.0, "maximum": 90.0},
            "longitude": {"type": "number", "minimum": -180.0, "maximum": 180.0},
        },
    }
    res = faker.process(
        OpenAPISpecification(source="default", api=spec(response_schema=schema)),
        request,
    )

    assert valid_schema(res.bodyAsJson, schema)


def test_sateless_faker_4(mock_data_store):
    faker = StatefulFaker(mock_data_store)

    request = RequestBuilder.from_dict(
        dict(method="get", protocol="http", path="/", host="api.com")
    )

    schema = {
        "$id": "https://example.com/arrays.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "description": "A representation of a person, company, organization, or place",
        "type": "object",
        "properties": {
            "fruits": {"type": "array", "items": {"type": "string"}},
            "vegetables": {
                "type": "array",
                "items": {"$ref": "#/components/schemas/veggie"},
            },
        },
    }
    components = {
        "schemas": {
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
        }
    }
    res = faker.process(
        OpenAPISpecification(
            source="default", api=spec(response_schema=schema, components=components)
        ),
        request,
    )

    schema["components"] = components
    assert valid_schema(res.bodyAsJson, schema)


def test_sateless_faker_5(mock_data_store):
    faker = StatefulFaker(mock_data_store)

    request = RequestBuilder.from_dict(
        dict(method="get", protocol="http", path="/", host="api.com")
    )

    schema = {"type": "array"}
    res = faker.process(
        OpenAPISpecification(source="default", api=spec(response_schema=schema)),
        request,
    )

    assert valid_schema(res.bodyAsJson, schema)
