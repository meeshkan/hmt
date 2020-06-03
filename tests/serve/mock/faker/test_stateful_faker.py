from http_types import RequestBuilder
from openapi_typed_2 import convert_to_OpenAPIObject

from hmt.serve.mock.faker.stateful_faker import StatefulFaker
from hmt.serve.mock.request_validation import valid_schema
from hmt.serve.mock.specs import OpenAPISpecification
from tests.util import spec, spec_dict


def test_fake_array(mock_data_store):
    faker = StatefulFaker(mock_data_store)

    request = RequestBuilder.from_dict(
        dict(method="get", protocol="http", path="/items", host="api.com")
    )

    schema = {"type": "array", "items": {"$ref": "#/components/schemas/item"}}

    components = {
        "schemas": {
            "item": {
                "type": "object",
                "required": ["foo", "bar"],
                "x-hmt-id-path": "itemId",
                "properties": {
                    "foo": {"type": "number"},
                    "bar": {"type": "string"},
                    "itemId": {"type": "string"},
                },
            }
        }
    }

    spec = spec_dict(
        path="/items", response_schema=schema, components=components, method="get"
    )
    spec["paths"]["/items"]["x-hmt-entity"] = "item"
    spec["paths"]["/items"]["get"]["x-hmt-operation"] = "read"

    spec = convert_to_OpenAPIObject(spec)
    mock_data_store.add_mock(OpenAPISpecification(spec, "default"))

    schema["components"] = components
    spec = OpenAPISpecification(source="default", api=spec)

    res = faker.process(spec, request)

    assert valid_schema(res.bodyAsJson, schema)
    assert 0 == len(res.bodyAsJson)

    mock_data_store["default"].item.insert({"foo": 10, "bar": "val", "itemId": "id123"})
    res = faker.process(spec, request)

    assert valid_schema(res.bodyAsJson, schema)
    assert 1 == len(res.bodyAsJson)

    mock_data_store["default"].item.insert(
        {"foo": 10, "bar": "val", "itemId": "id1234"}
    )
    res = faker.process(spec, request)

    assert valid_schema(res.bodyAsJson, schema)
    assert 2 == len(res.bodyAsJson)


def test_insert(mock_data_store):
    faker = StatefulFaker(mock_data_store)

    request_schema = {
        "type": "object",
        "properties": {"item": {"$ref": "#/components/schemas/item"}},
    }

    response_schema = {"$ref": "#/components/schemas/item"}

    components = {
        "schemas": {
            "item": {
                "type": "object",
                "required": ["foo"],
                "x-hmt-id-path": "itemId",
                "properties": {
                    "foo": {"type": "number"},
                    "bar": {"type": "string"},
                    "baz": {"type": "string"},
                    "itemId": {"type": "string"},
                },
            }
        }
    }

    spec = spec_dict(
        path="/items",
        request_schema=request_schema,
        response_schema=response_schema,
        components=components,
        method="post",
    )
    spec["paths"]["/items"]["x-hmt-entity"] = "item"
    spec["paths"]["/items"]["post"]["x-hmt-operation"] = "insert"

    spec = convert_to_OpenAPIObject(spec)
    mock_data_store.add_mock(OpenAPISpecification(spec, "default"))

    schema = response_schema
    schema["components"] = components
    spec = OpenAPISpecification(source="default", api=spec)

    request = RequestBuilder.from_dict(
        dict(
            method="post",
            protocol="http",
            path="/items",
            host="api.com",
            bodyAsJson={"item": {"foo": 10, "bar": "val"}},
        )
    )
    res = faker.process(spec, request)

    assert valid_schema(res.bodyAsJson, schema)
    assert res.bodyAsJson["itemId"] is not None
    assert 10 == res.bodyAsJson["foo"]

    assert 1 == len(mock_data_store["default"].item)
    assert "val" == mock_data_store["default"].item[res.bodyAsJson["itemId"]]["bar"]

    request = RequestBuilder.from_dict(
        dict(
            method="post",
            protocol="http",
            path="/items",
            host="api.com",
            bodyAsJson={"item": {"foo": 20, "bar": "val1", "itemId": "id123"}},
        )
    )
    res = faker.process(spec, request)

    assert valid_schema(res.bodyAsJson, schema)
    assert "id123" == res.bodyAsJson["itemId"]
    assert 20 == res.bodyAsJson["foo"]

    assert 2 == len(mock_data_store["default"].item)
    assert "val1" == mock_data_store["default"].item[res.bodyAsJson["itemId"]]["bar"]

    request = RequestBuilder.from_dict(
        dict(
            method="post",
            protocol="http",
            path="/items",
            host="api.com",
            bodyAsJson={"item": {"foo": 30, "itemId": "id123"}},
        )
    )
    res = faker.process(spec, request)

    assert 2 == len(mock_data_store["default"].item)
    assert "bar" not in mock_data_store["default"].item[res.bodyAsJson["itemId"]]
    assert 30 == mock_data_store["default"].item[res.bodyAsJson["itemId"]]["foo"]


def test_upsert(mock_data_store):
    faker = StatefulFaker(mock_data_store)

    response_schema = {
        "type": "object",
        "required": ["item"],
        "properties": {"item": {"$ref": "#/components/schemas/item"}},
    }

    request_schema = {"$ref": "#/components/schemas/item"}

    components = {
        "schemas": {
            "item": {
                "type": "object",
                "required": ["foo"],
                "x-hmt-id-path": "itemId",
                "properties": {
                    "foo": {"type": "number"},
                    "bar": {"type": "string"},
                    "baz": {"type": "string"},
                    "itemId": {"type": "string"},
                },
            }
        }
    }

    spec = spec_dict(
        path="/items",
        request_schema=request_schema,
        response_schema=response_schema,
        components=components,
        method="put",
    )
    spec["paths"]["/items"]["x-hmt-entity"] = "item"
    spec["paths"]["/items"]["put"]["x-hmt-operation"] = "upsert"

    spec = convert_to_OpenAPIObject(spec)
    mock_data_store.add_mock(OpenAPISpecification(spec, "default"))

    schema = response_schema
    schema["components"] = components
    spec = OpenAPISpecification(source="default", api=spec)

    request = RequestBuilder.from_dict(
        dict(
            method="put",
            protocol="http",
            path="/items",
            host="api.com",
            bodyAsJson={"foo": 10, "bar": "val"},
        )
    )
    res = faker.process(spec, request)

    assert valid_schema(res.bodyAsJson, schema)
    assert res.bodyAsJson["item"]["itemId"] is not None
    assert 10 == res.bodyAsJson["item"]["foo"]

    assert 1 == len(mock_data_store["default"].item)
    assert (
        "val"
        == mock_data_store["default"].item[res.bodyAsJson["item"]["itemId"]]["bar"]
    )

    request = RequestBuilder.from_dict(
        dict(
            method="put",
            protocol="http",
            path="/items",
            host="api.com",
            bodyAsJson={"foo": 20, "bar": "val1", "itemId": "id123"},
        )
    )
    res = faker.process(spec, request)

    assert valid_schema(res.bodyAsJson, schema)
    assert "id123" == res.bodyAsJson["item"]["itemId"]
    assert 20 == res.bodyAsJson["item"]["foo"]

    assert 2 == len(mock_data_store["default"].item)
    assert (
        "val1"
        == mock_data_store["default"].item[res.bodyAsJson["item"]["itemId"]]["bar"]
    )

    request = RequestBuilder.from_dict(
        dict(
            method="put",
            protocol="http",
            path="/items",
            host="api.com",
            bodyAsJson={"foo": 30, "itemId": "id123"},
        )
    )
    res = faker.process(spec, request)

    assert 2 == len(mock_data_store["default"].item)
    assert (
        "val1"
        == mock_data_store["default"].item[res.bodyAsJson["item"]["itemId"]]["bar"]
    )
    assert (
        30 == mock_data_store["default"].item[res.bodyAsJson["item"]["itemId"]]["foo"]
    )


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
