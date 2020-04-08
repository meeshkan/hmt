from meeshkan.serve.mock.storage.entity import Entity
from meeshkan.serve.mock.storage.mock_data import MockData
from openapi_typed_2 import convert_to_OpenAPIObject
from tests.util import spec_dict


def test_add():
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

    entity = Entity("item", spec)

    mock_data = MockData()
    mock_data.add_entity(entity)

    assert 0 == len(mock_data.item)
    assert "item" not in mock_data

    mock_data["item"] = "global"

    assert 0 == len(mock_data.item)
    assert "item" in mock_data
    assert "global" == mock_data["item"]


def test_clear():
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

    entity = Entity("item", spec)

    mock_data = MockData()
    mock_data.add_entity(entity)
    entity.insert({"foo": 10, "bar": "val", "itemId": "id123"})

    mock_data["global_data"] = "global"

    assert 1 == len(mock_data.item)
    assert "global_data" in mock_data

    mock_data.clear()

    assert 0 == len(mock_data.item)
    assert "global_data" not in mock_data
