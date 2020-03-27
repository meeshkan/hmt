from http_types import RequestBuilder
from meeshkan.serve.mock.storage.entity import Entity
from openapi_typed_2 import convert_to_OpenAPIObject
from tests.util import spec_dict


def test_insert():
    schema = {"$ref": "#/components/schemas/item"}

    components = {"schemas": {
        "item": {
            "type": "object",
            "required": ["foo", "baz"],
            "x-meeshkan-id-path": "itemId",
            "properties": {
                "foo": {"type": "number"},
                "bar": {"type": "string"},
                "itemId": {"type": "string"}
            }}}}

    spec = spec_dict(path="/items/{id}", response_schema=schema, components=components, method="get")
    spec["paths"]['/items/{id}']["x-meeshkan-entity"] = "item"
    spec["paths"]['/items/{id}']["get"]["x-meeshkan-operation"] = "read"

    spec = convert_to_OpenAPIObject(spec)

    entity = Entity("item", spec.components.schemas["item"])
    entity.add_path('/items/{id}', spec.paths['/items/{id}'])
    entity.insert({"foo": 10, "bar": "val", "itemId": "id123"})
    res = entity["id123"]
    assert 10 == res["foo"]


def test_insert_from_request():
    schema = {"$ref": "#/components/schemas/item"}

    components = {"schemas": {
        "item": {
            "type": "object",
            "required": ["foo", "baz"],
            "x-meeshkan-id-path": "itemId",
            "properties": {
                "foo": {"type": "number"},
                "bar": {"type": "string"},
                "itemId": {"type": "string"}
            }}}}

    spec = spec_dict(path="/items/create", response_schema=schema, request_schema=schema, components=components, method="post")
    spec["paths"]['/items/create']["x-meeshkan-entity"] = "item"
    spec["paths"]['/items/create']["post"]["x-meeshkan-operation"] = "insert"

    spec = convert_to_OpenAPIObject(spec)

    entity = Entity("item", spec.components.schemas["item"])
    entity.add_path('/items/create', spec.paths['/items/create'])
    request = RequestBuilder.from_dict(dict(method="post", protocol="http", path="/items", host="api.com",
                                            bodyAsJson={"foo": 10, "bar": "val", "itemId": "id123"}))

    entity.insert_from_request('/items/create', request)
    res = entity["id123"]
    assert 10 == res["foo"]