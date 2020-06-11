from dataclasses import replace
from typing import Callable, Optional, TypeVar, Union, cast

from lenses import lens
from openapi_typed_2 import (
    Any,
    Components,
    Mapping,
    OpenAPIObject,
    Parameter,
    Reference,
    RequestBody,
    Response,
    Schema,
    convert_from_openapi,
)

C = TypeVar("C")
D = TypeVar("D")
S = TypeVar("S")
T = TypeVar("T")
W = TypeVar("W")
X = TypeVar("X")
Y = TypeVar("Y")
Z = TypeVar("Z")


def get_component_from_ref(
    o: OpenAPIObject,
    d: str,
    accessor: Callable[[Components], Optional[Mapping[str, Union[Reference, C]]]],
    getter: Callable[[OpenAPIObject, Union[C, Reference]], Optional[C]],
) -> Optional[C]:
    return (
        lens.F(lambda a: a.components)
        .F(lambda a: a if a is None else accessor(a))
        .F(lambda a: a if a is None else getter(o, a[d]))
        .get()(o)
    )


def ref_name(r: Reference) -> str:
    return r._ref.split("/")[3]


def internal_get_component(
    f: Callable[[OpenAPIObject, str], Optional[C]]
) -> Callable[[OpenAPIObject, Union[C, Reference]], Optional[C]]:
    def _internal_get_component(
        o: OpenAPIObject, i: Union[C, Reference]
    ) -> Optional[C]:
        return (
            (f(o, ref_name(i)) if isinstance(i, Reference) else i)
            if i is not None
            else None
        )

    return _internal_get_component


# TODO: it seems that there is a bug in pyright that makes get_component_from_ref return a Union[Reference, Schema] instead of Schema
# need to do a cast of the output value to Schema (instead of the union) to fix that
# same for functions below
def get_schema_from_ref(o: OpenAPIObject, d: str) -> Optional[Schema]:
    out = get_component_from_ref(
        o, d, lambda a: a.schemas, internal_get_schema_from_ref
    )
    return None if out is None else cast(Schema, out)


internal_get_schema_from_ref = internal_get_component(get_schema_from_ref)


def get_parameter_from_ref(o: OpenAPIObject, d: str) -> Optional[Parameter]:
    out = get_component_from_ref(
        o, d, lambda a: a.parameters, internal_get_parameter_from_ref
    )
    return None if out is None else cast(Parameter, out)


internal_get_parameter_from_ref = internal_get_component(get_parameter_from_ref)


def get_request_body_from_ref(o: OpenAPIObject, d: str) -> Optional[RequestBody]:
    out = get_component_from_ref(
        o, d, lambda a: a.requestBodies, internal_get_request_body_from_ref
    )
    return None if out is None else cast(RequestBody, out)


internal_get_request_body_from_ref = internal_get_component(get_request_body_from_ref)


def get_response_from_ref(o: OpenAPIObject, d: str) -> Optional[Response]:
    out = get_component_from_ref(
        o, d, lambda a: a.responses, internal_get_response_from_ref
    )
    return None if out is None else cast(Response, out)


def get_response_body(o: OpenAPIObject, response):
    return (
        get_response_from_ref(o, ref_name(response))
        if isinstance(response, Reference)
        else response
    )


def get_request_body(o: OpenAPIObject, request):
    return (
        get_request_body_from_ref(o, ref_name(request))
        if isinstance(request, Reference)
        else request
    )


def get_parameter(o: OpenAPIObject, parameter):
    return (
        get_parameter_from_ref(o, ref_name(parameter))
        if isinstance(parameter, Reference)
        else parameter
    )


internal_get_response_from_ref = internal_get_component(get_response_from_ref)


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
