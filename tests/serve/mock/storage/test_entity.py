from http_types import RequestBuilder
from openapi_typed_2 import convert_to_OpenAPIObject
from tests.util import add_item, spec_dict

from mem.serve.mock.storage.entity import Entity


def test_insert():
    schema = {"$ref": "#/components/schemas/item"}

    components = {
        "schemas": {
            "item": {
                "type": "object",
                "required": ["foo", "baz"],
                "x-mem-id-path": "itemId",
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
    spec["paths"]["/items/{id}"]["x-mem-entity"] = "item"
    spec["paths"]["/items/{id}"]["get"]["x-mem-operation"] = "read"

    spec = convert_to_OpenAPIObject(spec)

    entity = Entity("item", spec)
    entity.insert({"foo": 10, "bar": "val", "itemId": "id123"})
    res = entity["id123"]
    assert 10 == res["foo"]


def test_insert_from_request():
    schema = {"$ref": "#/components/schemas/item"}

    components = {
        "schemas": {
            "item": {
                "type": "object",
                "required": ["foo", "baz"],
                "x-mem-id-path": "itemId",
                "properties": {
                    "foo": {"type": "number"},
                    "bar": {"type": "string"},
                    "itemId": {"type": "string"},
                },
            }
        }
    }

    spec = spec_dict(
        path="/items/create",
        response_schema=schema,
        request_schema=schema,
        components=components,
        method="post",
    )
    spec["paths"]["/items/create"]["x-mem-entity"] = "item"
    spec["paths"]["/items/create"]["post"]["x-mem-operation"] = "insert"

    spec = convert_to_OpenAPIObject(spec)

    entity = Entity("item", spec)

    request = RequestBuilder.from_dict(
        dict(
            method="post",
            protocol="http",
            path="/items",
            host="api.com",
            bodyAsJson={"foo": 15, "bar": "val2"},
        )
    )

    entity.insert_from_request("/items/create", request)
    res = next(iter(entity.values()))
    assert 15 == res["foo"]
    assert res["itemId"] is not None

    request = RequestBuilder.from_dict(
        dict(
            method="post",
            protocol="http",
            path="/items",
            host="api.com",
            bodyAsJson={"foo": 10, "bar": "val", "itemId": "id123"},
        )
    )

    entity.insert_from_request("/items/create", request)
    assert len(entity) == 2
    res = entity["id123"]
    assert 10 == res["foo"]


def test_upsert_from_request():
    schema = {"$ref": "#/components/schemas/item"}

    components = {
        "schemas": {
            "item": {
                "type": "object",
                "required": ["foo", "baz"],
                "x-mem-id-path": "itemId",
                "properties": {
                    "foo": {"type": "number"},
                    "bar": {"type": "string"},
                    "itemId": {"type": "string"},
                },
            }
        }
    }

    spec = spec_dict(
        path="/items/create",
        response_schema=schema,
        request_schema=schema,
        components=components,
        method="post",
    )
    spec["paths"]["/items/create"]["x-mem-entity"] = "item"
    spec["paths"]["/items/create"]["post"]["x-mem-operation"] = "insert"

    spec = convert_to_OpenAPIObject(spec)

    entity = Entity("item", spec)

    request = RequestBuilder.from_dict(
        dict(
            method="post",
            protocol="http",
            path="/items",
            host="api.com",
            bodyAsJson={"foo": 15, "bar": "val2"},
        )
    )

    entity.insert_from_request("/items/create", request)
    res = next(iter(entity.values()))
    assert 15 == res["foo"]
    assert res["itemId"] is not None

    request = RequestBuilder.from_dict(
        dict(
            method="post",
            protocol="http",
            path="/items",
            host="api.com",
            bodyAsJson={"foo": 10, "bar": "val", "itemId": res["itemId"]},
        )
    )

    entity.upsert_from_request("/items/create", request)
    assert len(entity) == 1
    res = next(iter(entity.values()))
    assert 10 == res["foo"]


def test_query():
    schema_single = {"$ref": "#/components/schemas/item"}
    schema_array = {
        "accounts": {"items": {"$ref": "#/components/schemas/items"}, "type": "array"}
    }

    components = {
        "schemas": {
            "item": {
                "type": "object",
                "required": ["foo", "baz"],
                "x-mem-id-path": "itemId",
                "properties": {
                    "foo": {"type": "number"},
                    "bar": {"type": "string"},
                    "itemId": {"type": "string"},
                },
            }
        }
    }

    spec = spec_dict(
        path="/items/{id}",
        response_schema=schema_single,
        components=components,
        method="get",
    )
    spec["paths"]["/items/{id}"]["x-mem-entity"] = "item"
    spec["paths"]["/items/{id}"]["get"]["x-mem-operation"] = "read"

    add_item(
        spec,
        path="/items",
        response_schema=schema_array,
        components=components,
        method="get",
    )
    spec["paths"]["/items"]["x-mem-entity"] = "item"
    spec["paths"]["/items"]["get"]["x-mem-operation"] = "read"

    spec = convert_to_OpenAPIObject(spec)

    entity = Entity("item", spec)

    entity.insert({"foo": 10, "bar": "val", "itemId": "id123"})
    entity.insert({"foo": 20, "bar": "val1", "itemId": "id1234"})
    entity.insert({"foo": 30, "bar": "val2", "itemId": "id12345"})

    res = entity.query_one(
        "/items/{id}",
        RequestBuilder.from_dict(
            dict(method="get", protocol="http", path="/items/id1234", host="api.com")
        ),
    )

    assert 20 == res["foo"]

    res = entity.query(
        "/items",
        RequestBuilder.from_dict(
            dict(method="get", protocol="http", path="/items", host="api.com")
        ),
    )

    assert 3 == len(res)
