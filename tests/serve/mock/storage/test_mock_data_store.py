from openapi_typed_2 import convert_to_OpenAPIObject
from tests.util import spec, spec_dict

from meeshkan.serve.mock.specs import OpenAPISpecification
from meeshkan.serve.mock.storage.mock_data_store import MockDataStore


def test_add_mock_no_data():
    schema = {"$ref": "#/components/schemas/item"}

    components = {
        "schemas": {
            "item": {
                "type": "object",
                "required": ["foo", "baz"],
                "x-meeshkan-id-path": "itemId",
                "properties": {
                    "foo": {"type": "number"},
                    "bar": {"type": "string"},
                    "itemId": {"type": "string"},
                },
            }
        }
    }

    spec = spec_dict(
        path="/items/{id}", response_schema=schema, components=components, method="get"
    )
    spec["paths"]["/items/{id}"]["x-meeshkan-entity"] = "item"
    spec["paths"]["/items/{id}"]["get"]["x-meeshkan-operation"] = "read"

    spec = convert_to_OpenAPIObject(spec)

    store = MockDataStore()
    store.add_mock(OpenAPISpecification(spec, "items"))

    assert 0 == len(store["items"].item)

    store["items"].item.insert({"foo": 10, "bar": "val", "itemId": "id123"})

    assert 1 == len(store["items"].item)
    assert "val" == store["items"].item["id123"]["bar"]


def test_add_mock_data():
    schema = {"$ref": "#/components/schemas/item"}

    components = {
        "schemas": {
            "item": {
                "type": "object",
                "required": ["foo", "baz"],
                "x-meeshkan-id-path": "itemId",
                "properties": {
                    "foo": {"type": "number"},
                    "bar": {"type": "string"},
                    "itemId": {"type": "string"},
                },
            }
        }
    }

    spec = spec_dict(
        path="/items/{id}", response_schema=schema, components=components, method="get"
    )
    spec["paths"]["/items/{id}"]["x-meeshkan-entity"] = "item"
    spec["paths"]["/items/{id}"]["get"]["x-meeshkan-operation"] = "read"
    spec["x-meeshkan-data"] = {}
    spec["x-meeshkan-data"]["item"] = [
        {"foo": 10, "bar": "val", "itemId": "id123"},
        {"foo": 20, "bar": "val1", "itemId": "id1234"},
    ]
    spec = convert_to_OpenAPIObject(spec)

    store = MockDataStore()
    store.add_mock(OpenAPISpecification(spec, "items"))

    assert 2 == len(store["items"].item)
    assert "val1" == store["items"].item["id1234"]["bar"]


def test_clear():
    store = MockDataStore()

    store.add_mock(OpenAPISpecification(spec(), "pokemon"))
    store.add_mock(OpenAPISpecification(spec(), "another"))

    store["pokemon"]["x"] = "foo"
    store["another"]["y"] = "bar"

    assert "foo" == store["pokemon"]["x"]
    assert "bar" == store["another"]["y"]

    store.clear()

    assert store["pokemon"].get("x") is None
    assert store["another"].get("y") is None


def test_reset():
    schema = {"$ref": "#/components/schemas/item"}

    components = {
        "schemas": {
            "item": {
                "type": "object",
                "required": ["foo", "baz"],
                "x-meeshkan-id-path": "itemId",
                "properties": {
                    "foo": {"type": "number"},
                    "bar": {"type": "string"},
                    "itemId": {"type": "string"},
                },
            }
        }
    }

    spec = spec_dict(
        path="/items/{id}", response_schema=schema, components=components, method="get"
    )
    spec["paths"]["/items/{id}"]["x-meeshkan-entity"] = "item"
    spec["paths"]["/items/{id}"]["get"]["x-meeshkan-operation"] = "read"
    spec["x-meeshkan-data"] = {"item": [{"foo": 10, "bar": "val", "itemId": "id123"}]}
    spec = convert_to_OpenAPIObject(spec)

    store = MockDataStore()
    store.add_mock(OpenAPISpecification(spec, "items"))

    assert 1 == len(store["items"].item)

    store["items"].item.insert({"foo": 10, "bar": "val1", "itemId": "id1234"})

    assert 2 == len(store["items"].item)
    assert "val1" == store["items"].item["id1234"]["bar"]

    store.reset()

    assert 1 == len(store["items"].item)
    assert "val" == store["items"].item["id123"]["bar"]
