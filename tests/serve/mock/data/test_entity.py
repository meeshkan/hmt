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
            "properties": {
                "foo": {"type": "number"},
                "bar": {"type": "string"},
                "itemId": {"type": "string"}
            }}}}

    spec = spec_dict(path="/items/{id}", response_schema=schema, components=components, method="get")
    spec["paths"]['/items/{id}']["x-meeshkan-entity"] = "item"
    spec["paths"]['/items/{id}']["x-meeshkan-id-path"] = "itemId"
    spec["paths"]['/items/{id}']["get"]["x-meeshkan-operation"] = "read"

    spec = convert_to_OpenAPIObject(spec)

    entity = Entity('/items/{id}', spec.paths['/items/{id}'])
    entity.insert({"foo": 10, "bar": "val", "itemId": "id123"})
    res = entity["id123"]
    assert 10 == res["foo"]


def test_insert_from_request():
    schema = {"$ref": "#/components/schemas/item"}

    components = {"schemas": {
        "item": {
            "type": "object",
            "required": ["foo", "baz"],
            "properties": {
                "foo": {"type": "number"},
                "bar": {"type": "string"},
                "itemId": {"type": "string"}
            }}}}

    spec = spec_dict(path="/items/create", response_schema=schema, components=components, method="post")
    spec["paths"]['/items/{id}']["x-meeshkan-entity"] = "item"
    spec["paths"]['/items/{id}']["x-meeshkan-id-path"] = "itemId"
    spec["paths"]['/items/{id}']["get"]["x-meeshkan-operation"] = "insert"

    spec = convert_to_OpenAPIObject(spec)

    entity = Entity('/items/{id}', spec.paths['/items/{id}'])

    request = RequestBuilder.from_dict(dict(method="get", protocol="http", path="/", host="api.com"))

    entity.insert_from_request()
    entity.insert({"foo": 10, "bar": "val", "itemId": "id123"})
    res = entity["id123"]
    assert 10 == res["foo"]