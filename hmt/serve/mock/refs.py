from dataclasses import replace

from openapi_typed_2 import (
    Any,
    Mapping,
    OpenAPIObject,
    Reference,
    Schema,
    convert_from_openapi,
)


def ref_name(r: Reference) -> str:
    return r._ref.split("/")[3]


def change_ref(j: Reference) -> Reference:
    return Reference(_x=None, _ref="#/definitions/%s" % ref_name(j),)


def change_refs(j: Schema) -> Schema:
    return replace(
        j,
        additionalProperties=None
        if j.additionalProperties is None
        else j.additionalProperties
        if isinstance(j.additionalProperties, bool)
        else change_ref(j.additionalProperties)
        if isinstance(j.additionalProperties, Reference)
        else change_refs(j.additionalProperties),
        items=None
        if j.items is None
        else change_ref(j.items)
        if isinstance(j.items, Reference)
        else change_refs(j.items)
        if isinstance(j.items, Schema)
        else [
            change_ref(item) if isinstance(item, Reference) else change_refs(item)
            for item in j.items
        ],
        _not=None
        if j._not is None
        else change_ref(j._not)
        if isinstance(j._not, Reference)
        else change_refs(j._not),
        anyOf=None
        if j.anyOf is None
        else [
            change_ref(item) if isinstance(item, Reference) else change_refs(item)
            for item in j.anyOf
        ],
        allOf=None
        if j.allOf is None
        else [
            change_ref(item) if isinstance(item, Reference) else change_refs(item)
            for item in j.allOf
        ],
        oneOf=None
        if j.oneOf is None
        else [
            change_ref(item) if isinstance(item, Reference) else change_refs(item)
            for item in j.oneOf
        ],
        properties=None
        if j.properties is None
        else {
            k: change_ref(v) if isinstance(v, Reference) else change_refs(v)
            for k, v in j.properties.items()
        },
    )


def make_definitions_from_spec(o: OpenAPIObject) -> Mapping[str, Any]:
    return (
        {
            a: convert_from_openapi(
                change_ref(b) if isinstance(b, Reference) else change_refs(b)
            )
            for a, b in o.components.schemas.items()
        }
        if o.components and o.components.schemas
        else {}
    )
