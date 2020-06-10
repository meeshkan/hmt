import json
import logging
from dataclasses import replace
from functools import reduce
from typing import Any, Callable, Mapping, Optional, Sequence, TypeVar, Union, cast

import jsonschema
import lenses
from http_types import Request
from lenses import lens
from openapi_typed_2 import (
    Components,
    Header,
    MediaType,
    OpenAPIObject,
    Operation,
    Parameter,
    PathItem,
    Reference,
    RequestBody,
    Response,
    Responses,
    Schema,
    convert_from_openapi,
)

from hmt.serve.mock.refs import (
    change_ref,
    change_refs,
    get_request_body,
    make_definitions_from_spec,
    ref_name,
)
from hmt.serve.mock.specs import OpenAPISpecification

C = TypeVar("C")
D = TypeVar("D")
S = TypeVar("S")
T = TypeVar("T")
W = TypeVar("W")
X = TypeVar("X")
Y = TypeVar("Y")
Z = TypeVar("Z")

# def pp(s, c: C) -> C:
#    print(s, c)
#    return c

all_methods: Sequence[str] = [
    "get",
    "post",
    "put",
    "delete",
    "options",
    "head",
    "patch",
    "trace",
]

logger = logging.getLogger(__name__)

_prism_o = (lambda a: a, lambda b: b)


def odl(
    getter: Callable[[C], D], setter: Callable[[C, D], C]
) -> lenses.ui.BaseUiLens[S, T, X, Y]:
    # TODO: is there a better `None` prism?
    # Seems verbose
    return lens.Lens(getter, setter).Prism(lambda a: a, lambda a: a, ignore_none=True)


def _schema_o_setter(a: C, b: Optional[Schema]):
    return replace(a, schema=b)


schema_o = odl(lambda a: a.schema, _schema_o_setter)


def _request_body_o_setter(a: C, b: Optional[RequestBody]):
    return replace(a, requestBody=b)


request_body_o = odl(lambda a: a.requestBody, _request_body_o_setter)


def _content_o_setter(a: C, b: Optional[Mapping[str, MediaType]]):
    return replace(a, content=b)


content_o = odl(lambda a: a.content, _content_o_setter)


def _paths_o_setter(a: C, b: Optional[Mapping[str, PathItem]]):
    return replace(a, paths=b)


paths_o = odl(lambda a: a.paths, _paths_o_setter)


def _headers_o_setter(a: C, b: Optional[Mapping[str, Union[Header, Reference]]]):
    return replace(a, headers=b)


headers_o = odl(lambda a: a.headers, _headers_o_setter)


def _responses_o(a: C, b: Responses):
    return replace(a, responses=b)


responses_o = odl(lambda a: a.responses, _responses_o)


def _parameters_o_setter(a: C, b: Optional[Sequence[Parameter]]):
    return replace(a, parameters=b)


parameters_o = odl(lambda a: a.parameters, _parameters_o_setter)


def _get_o_setter(a: C, b: Optional[Operation]):
    return replace(a, get=b)


def _post_o_setter(a: C, b: Optional[Operation]):
    return replace(a, post=b)


def _put_o_setter(a: C, b: Optional[Operation]):
    return replace(a, put=b)


def _delete_o_setter(a: C, b: Optional[Operation]):
    return replace(a, delete=b)


def _options_o_setter(a: C, b: Optional[Operation]):
    return replace(a, options=b)


def _head_o_setter(a: C, b: Optional[Operation]):
    return replace(a, head=b)


def _patch_o_setter(a: C, b: Optional[Operation]):
    return replace(a, patch=b)


def _trace_o_setter(a: C, b: Optional[Operation]):
    return replace(a, trace=b)


def operation_o(m: str):
    return {
        "get": odl(lambda a: a.get, _get_o_setter),
        "post": odl(lambda a: a.post, _post_o_setter),
        "put": odl(lambda a: a.put, _put_o_setter),
        "delete": odl(lambda a: a.delete, _delete_o_setter),
        "options": odl(lambda a: a.options, _options_o_setter),
        "head": odl(lambda a: a.head, _head_o_setter),
        "patch": odl(lambda a: a.patch, _patch_o_setter),
        "trace": odl(lambda a: a.trace, _trace_o_setter),
    }[m]


def oll(focus: int) -> lenses.ui.BaseUiLens[S, T, X, Y]:
    """Focus on a specific index in an array if it exists
    """
    return lens.Items().Filter(lambda a: a[0] == focus)[1]


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


internal_get_response_from_ref = internal_get_component(get_response_from_ref)


def schema_prism(oai: OpenAPIObject) -> lenses.ui.BaseUiLens[S, T, X, Y]:
    return lens.Prism(
        lambda s: get_schema_from_ref(oai, ref_name(s))
        if isinstance(s, Reference)
        else s,
        lambda a: a,
        ignore_none=True,
    )


#
# def find_relevant_path(m: str, a: Sequence[str], p: PathItem) -> PathItem:
#     return (
#         p
#         if len(a) == 0
#         else find_relevant_path(
#             m, a[1:], p if a[0] == m else omit_method_from_path_item(p, a[0]),
#         )
#     )


# def get_path_item_with_method(m: str, p: PathItem) -> PathItem:
#     return find_relevant_path(m, all_methods, p)
#


def get_required_request_query_or_header_parameters_internal(
    header: bool, l: lenses.ui.BaseUiLens[S, T, X, Y], oai: OpenAPIObject, p: PathItem
) -> Sequence[Parameter]:
    # TODO: really dirty cast
    # is this even the case
    # copied from unmock, but need to investigate
    return [
        replace(
            parameter,
            name=parameter.name if not header else parameter.name.lower(),
            schema=change_ref(parameter.schema)
            if isinstance(parameter.schema, Reference)
            else change_refs(parameter.schema)
            if parameter.schema is not None
            else Schema(_type="string"),
        )
        for parameter in l.Prism(
            lambda s: get_parameter_from_ref(oai, ref_name(s))
            if isinstance(s, Reference)
            else s,
            lambda a: a,
            ignore_none=True,
        )
        .Prism(
            lambda s: s
            if (s._in == ("header" if header else "query")) and s.required
            else None,
            lambda a: a,
            ignore_none=True,
        )
        .collect()(p)
        if parameter.schema is not None
        and (
            len(lens.Each().add_lens(schema_prism(oai)).collect()([parameter.schema]))
            > 0
        )
    ]


def get_required_request_query_or_header_parameters(
    header: bool, req: Request, oai: OpenAPIObject, p: PathItem
) -> Sequence[Parameter]:
    return [
        *get_required_request_query_or_header_parameters_internal(
            header, parameters_o.Each(), oai, p
        ),
        *get_required_request_query_or_header_parameters_internal(
            header, operation_o(req.method.value).add_lens(parameters_o).Each(), oai, p
        ),
    ]


def valid_schema(to_validate: Any, schema: Any) -> bool:
    try:
        jsonschema.validate(to_validate, schema)
        return True
    except Exception as e:
        return False


def _json_schema_from_required_parameters(
    parameters: Sequence[Parameter], oai: OpenAPIObject
) -> Any:
    return {
        "type": "object",
        "properties": {
            param.name: convert_from_openapi(param.schema) for param in parameters
        },
        "required": [param.name for param in parameters if param.required],
        "additionalProperties": True,
        "definitions": make_definitions_from_spec(oai),
    }


def maybe_add_string_schema(
    s: Sequence[Union[Reference, Schema]]
) -> Sequence[Union[Reference, Schema]]:
    return [Schema(_type="string")] if len(s) == 0 else s


def discern_name(o: Optional[Parameter], n: str) -> Optional[Parameter]:
    return o if (o is None) or ((o.name == n) and (o._in == "path")) else None


def internal_get_parameter_schemas(
    t: lenses.ui.BaseUiLens[S, T, X, Y],
    vname: str,
    path_item: PathItem,
    oas: OpenAPIObject,
) -> Sequence[Schema]:
    return (
        t.Prism(
            lambda i: discern_name(get_parameter_from_ref(oas, ref_name(i)), vname)
            if isinstance(i, Reference)
            else discern_name(i, vname),
            lambda a: a,
            ignore_none=True,
        )
        .add_lens(schema_o)
        .collect()(path_item)
    )


def path_item_path_parameter_schemas(
    vname: str, path_item: PathItem, oas: OpenAPIObject,
) -> Sequence[Schema]:
    return internal_get_parameter_schemas(parameters_o.Each(), vname, path_item, oas,)


def operation_path_parameter_schemas(
    vname: str, path_item: PathItem, operation: str, oas: OpenAPIObject,
) -> Sequence[Schema]:
    return internal_get_parameter_schemas(
        operation_o(operation.lower()).add_lens(parameters_o).Each(),
        vname,
        path_item,
        oas,
    )


def get_matching_parameters(
    vname: str, path_item: PathItem, operation: str, oas: OpenAPIObject,
) -> Sequence[Union[Schema, Reference]]:
    return maybe_add_string_schema(
        [
            *path_item_path_parameter_schemas(vname, path_item, oas),
            *operation_path_parameter_schemas(vname, path_item, operation, oas),
        ]
    )


def maybeJson(maybe: str) -> Any:
    try:
        return json.loads(maybe)
    except json.JSONDecodeError:
        return maybe


def path_parameter_match(
    part: str, vname: str, path_item: PathItem, operation: str, oas: OpenAPIObject,
) -> bool:
    """Matches part of a path against a path parameter with name vname

    Arguments:
        part {str} -- part of a path, ie an id
        vname {str} -- name of a parameter
        path_item {PathItem} -- a path item maybe containing the parameter
        operation {MethodNames} -- the name of the operation to check in case the parameter is in the operation
        oas {OpenAPIObject} -- the schema to traverse to find definitions

    Returns:
        bool -- Did we get a match
    """
    return reduce(
        lambda q, r: q
        and reduce(
            lambda a, b: a
            or valid_schema(
                b,
                {
                    **convert_from_openapi(r),
                    "definitions": make_definitions_from_spec(oas),
                },
            ),
            list(set([part, maybeJson(part)])),
            False,
        ),
        get_matching_parameters(vname, path_item, operation, oas),
        True,
    )


def validate_params(
    header: bool, req: Request, oai: OpenAPIObject, p: PathItem
) -> bool:
    return valid_schema(
        {k.lower(): v for k, v in req.headers.items()} if header else req.query,
        _json_schema_from_required_parameters(
            get_required_request_query_or_header_parameters(header, req, oai, p), oai,
        ),
    )


def validate_query_params(req: Request, oai: OpenAPIObject, p: PathItem) -> bool:
    return validate_params(False, req, oai, p)


def validate_header_params(req: Request, oai: OpenAPIObject, p: PathItem) -> bool:
    return validate_params(True, req, oai, p)


def validate_body(req: Request, spec: OpenAPISpecification, op: Operation) -> bool:
    request_body = get_request_body(spec.api, op.requestBody)
    if (
        request_body is not None
        and "application/json" in request_body.content
        and request_body.content["application/json"].schema
    ):
        schema = cast(
            Union[Schema, Reference], request_body.content["application/json"].schema
        )
        return valid_schema(
            req.bodyAsJson,
            {
                **convert_from_openapi(
                    change_ref(schema)
                    if isinstance(schema, Reference)
                    else change_refs(schema)
                ),
                "definitions": spec.definitions,
            },
        )

    return True
