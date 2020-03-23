import json
import re
from dataclasses import replace
from functools import reduce
from typing import (
    Any,
    Callable,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
)
from urllib.parse import urlparse

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

from meeshkan.build.operation import operation_from_string
from meeshkan.serve.mock.specs import OpenAPISpecification

C = TypeVar("C")
D = TypeVar("D")
S = TypeVar("S")
T = TypeVar("T")
W = TypeVar("W")
X = TypeVar("X")
Y = TypeVar("Y")
Z = TypeVar("Z")

__all__ = ["match_request_to_openapi", "change_ref", "change_refs"]


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


def omit_method_from_path_item(p: PathItem, a: str) -> PathItem:
    return (
        replace(p, get=None)
        if a == "get"
        else replace(p, post=None)
        if a == "post"
        else replace(p, put=None)
        if a == "put"
        else replace(p, delete=None)
        if a == "delete"
        else replace(p, patch=None)
        if a == "patch"
        else replace(p, trace=None)
        if a == "trace"
        else replace(p, options=None)
        if a == "options"
        else replace(p, head=None)
    )


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


def match_urls(protocol: str, host: str, o: OpenAPIObject) -> Sequence[str]:
    """Finds mock URLs that match a given protocol and host.

    Arguments:
        protocol {str} -- like http or https
        host {str} -- like api.foo.com
        o {OpenAPIObject} -- schema from which the mock URLs are taken

    Returns:
        A list of URLs that match the OpenAPI spec.
    """
    servers = o.servers
    if servers is None:
        return []
    #### if the openapi mock url has no scheme,
    #### we ignore the incoming scheme and treat the url as the host
    #### not sure if this is the right decision,
    #### but it deals with a realistic outcome in certain schemas
    return [
        server.url
        for server in servers
        if (
            (urlparse(server.url).scheme in ["", None])
            or (urlparse(server.url).scheme == protocol)
        )
        and (
            (server.url.split("/")[0] == host) or (urlparse(server.url).netloc == host)
        )
    ]


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


internal_get_response_from_ref = internal_get_component(get_response_from_ref)


def schema_prism(oai: OpenAPIObject) -> lenses.ui.BaseUiLens[S, T, X, Y]:
    return lens.Prism(
        lambda s: get_schema_from_ref(oai, ref_name(s))
        if isinstance(s, Reference)
        else s,
        lambda a: a,
        ignore_none=True,
    )


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


def make_definitions_from_schema(o: OpenAPIObject) -> Mapping[str, Any]:
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


def find_relevant_path(m: str, a: Sequence[str], p: PathItem) -> PathItem:
    return (
        p
        if len(a) == 0
        else find_relevant_path(
            m, a[1:], p if a[0] == m else omit_method_from_path_item(p, a[0]),
        )
    )


def get_path_item_with_method(m: str, p: PathItem) -> PathItem:
    return find_relevant_path(m, all_methods, p)


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


def get_required_request_body_schemas(
    req: Request, oai: OpenAPIObject, p: PathItem,
) -> Sequence[Union[Reference, Schema]]:
    return (
        operation_o(req.method.value)
        .add_lens(request_body_o)
        .Prism(
            lambda s: get_request_body_from_ref(oai, ref_name(s))
            if isinstance(s, Reference)
            else s,
            lambda a: a,
            ignore_none=True,
        )
        # automatically ignore not required for now
        .Prism(
            lambda s: None if s.required is False else s, lambda a: a, ignore_none=True
        )
        .add_lens(content_o)
        .Values()
        .add_lens(schema_o)
        .add_lens(schema_prism(oai))
        .collect()(p)
    )


def valid_schema(to_validate: Any, schema: Any) -> bool:
    try:
        jsonschema.validate(to_validate, schema)
        return True
    except Exception:
        # print(e)
        return False


def keep_method_if_required_request_body_is_present(
    req: Request, oai: OpenAPIObject,
) -> Callable[[PathItem], PathItem]:
    def _keep_method_if_required_request_body_is_present(p: PathItem) -> PathItem:
        out = (
            p
            if (operation_from_string(p, req.method.value) is None)
            or (
                len(
                    [
                        s
                        for s in get_required_request_body_schemas(req, oai, p)
                        if not valid_schema(
                            req.bodyAsJson
                            if req.bodyAsJson is not None
                            else json.loads(req.body)
                            if req.body is not None
                            else "",
                            {
                                # TODO: this line is different than the TS implementation
                                # because I think there is a logic bug there
                                # it should look like this line as we are not sure
                                # if the schema will be a reference or not
                                # perhaps I'm wrong in the assumption... only testing will tell...
                                # otherwise, change the TS implementation in unmock-js and delete this comment.
                                **convert_from_openapi(
                                    change_ref(s)
                                    if isinstance(s, Reference)
                                    else change_refs(s)
                                ),
                                "definitions": make_definitions_from_schema(oai),
                            },
                        )
                    ]
                )
                == 0
            )
            else omit_method_from_path_item(p, req.method.value)
        )
        return out

    return _keep_method_if_required_request_body_is_present


def keep_method_if_required_header_parameters_are_present(
    req: Request, oai: OpenAPIObject,
) -> Callable[[PathItem], PathItem]:
    def _keep_method_if_required_header_parameters_are_present(p: PathItem) -> PathItem:
        out = keep_method_if_required_query_or_header_parameters_are_present(
            True, req, oai, p
        )
        return out

    return _keep_method_if_required_header_parameters_are_present


def keep_method_if_required_query_parameters_are_present(
    req: Request, oai: OpenAPIObject,
) -> Callable[[PathItem], PathItem]:
    def _keep_method_if_required_query_parameters_are_present(p: PathItem) -> PathItem:
        out = keep_method_if_required_query_or_header_parameters_are_present(
            False, req, oai, p
        )
        return out

    return _keep_method_if_required_query_parameters_are_present


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
        "definitions": make_definitions_from_schema(oai),
    }


def keep_method_if_required_query_or_header_parameters_are_present(
    header: bool, req: Request, oai: OpenAPIObject, p: PathItem
) -> PathItem:
    return (
        p
        if (operation_from_string(p, req.method.value) is None)
        or valid_schema(
            {k.lower(): v for k, v in req.headers.items()} if header else req.query,
            _json_schema_from_required_parameters(
                get_required_request_query_or_header_parameters(header, req, oai, p),
                oai,
            ),
        )
        else omit_method_from_path_item(p, req.method.value)
    )


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
                    "definitions": make_definitions_from_schema(oas),
                },
            ),
            list(set([part, maybeJson(part)])),
            False,
        ),
        get_matching_parameters(vname, path_item, operation, oas),
        True,
    )


path_param_regex = re.compile(r"^\{[^}]+\}")


# TODO: this is a boolean nightmare
# what we want is
# lengths_are_equal AND (empty OR ((first_elt_equal OR (matches_regex AND matches_schema)) AND recursion))
def matches_internal(
    path: Sequence[str],
    path_item_key: Sequence[str],
    path_item: PathItem,
    operation: str,
    o: OpenAPIObject,
) -> bool:
    return (len(path) == len(path_item_key)) and (
        (len(path) == 0)
        or (
            (
                (path[0] == path_item_key[0])
                or (
                    (path_param_regex.match(path_item_key[0]) is not None)
                    and path_parameter_match(
                        path[0], path_item_key[0][1:-1], path_item, operation, o,
                    )
                )
            )
            and matches_internal(path[1:], path_item_key[1:], path_item, operation, o,)
        )
    )


def matches(
    path: str, path_item_key: str, path_item: PathItem, method: str, oas: OpenAPIObject,
) -> bool:
    return matches_internal(
        [x for x in path.split("/") if x != ""],
        [x for x in path_item_key.split("/") if x != ""],
        path_item,
        method,
        oas,
    )


def get_first_method_internal_2(
    p: PathItem, n: str, m: Sequence[str], o: Optional[Operation],
) -> Optional[Tuple[str, Operation]]:
    return (n, o) if o is not None else get_first_method_internal(m, p)


def get_first_method_internal(
    m: Sequence[str], p: PathItem,
) -> Optional[Tuple[str, Operation]]:
    return (
        None
        if len(m) == 0
        else get_first_method_internal_2(p, m[0], m[1:], operation_from_string(p, m[0]))
    )


def get_first_method(p: PathItem) -> Optional[Tuple[str, Operation]]:
    return get_first_method_internal(all_methods, p)


def get_header_from_ref(o: OpenAPIObject, d: str) -> Optional[Header]:
    out = get_component_from_ref(
        o, d, lambda a: a.headers, internal_get_header_from_ref,
    )
    return None if out is None else cast(Header, out)


internal_get_header_from_ref = internal_get_component(get_header_from_ref)


def use_if_header_last_mile(
    p: Parameter, r: Optional[Schema],
) -> Optional[Tuple[str, Schema]]:
    return (
        None if r is None else (p.name, r if r is not None else Schema(_type="string"))
    )


def use_if_header(o: OpenAPIObject, p: Parameter,) -> Optional[Tuple[str, Schema]]:
    return (
        None
        if p._in != "header"
        else use_if_header_last_mile(
            p,
            Schema(_type="string")
            if p.schema is None
            else get_schema_from_ref(o, ref_name(p.schema))
            if isinstance(p.schema, Reference)
            else p.schema,
        )
    )


def parameter_schema(o: OpenAPIObject) -> lenses.ui.BaseUiLens[S, T, X, Y]:
    return lens.Iso(lambda a: (use_if_header(o, a), a), lambda b: b[1])[0].Prism(
        *_prism_o, ignore_none=True
    )


def cut_path(paths: Sequence[str], path: str) -> str:
    return (
        path
        if len(paths) == 0
        else path[len(paths[0]) :]
        if path[: len(paths[0])] == paths[0]
        else cut_path(paths[1:], path)
    )


def remove_trailing_slash(s: str) -> str:
    return s if len(s) == 0 else s[:-1] if s[-1] == "/" else s


def truncate_path(path: str, o: OpenAPIObject, i: Request,) -> str:
    return cut_path(
        [
            remove_trailing_slash(urlparse(u).path)
            for u in match_urls(i.protocol.value, i.host, o)
        ],
        path,
    )


def match_request_to_openapi(
    req: Request, specs: Sequence[OpenAPISpecification]
) -> Sequence[OpenAPISpecification]:
    def _path_item_modifier(oai: OpenAPIObject) -> Callable[[PathItem], PathItem]:
        def __path_item_modifier(path_item: PathItem) -> PathItem:
            return reduce(
                lambda a, b: b(a),
                [
                    keep_method_if_required_header_parameters_are_present(req, oai),
                    keep_method_if_required_query_parameters_are_present(req, oai),
                    keep_method_if_required_request_body_is_present(req, oai),
                ],
                get_path_item_with_method(req.method.value, path_item),
            )

        return __path_item_modifier

    def _oai_modifier(oai: OpenAPIObject) -> OpenAPIObject:
        return paths_o.Values().modify(_path_item_modifier(oai))(
            replace(
                oai,
                paths={
                    n: o
                    for n, o in oai.paths.items()
                    if matches(
                        truncate_path(req.pathname, oai, req),
                        n,
                        o,
                        req.method.value,
                        oai,
                    )
                },
            )
        )

    specs_with_matching_urls = {
        spec.source: spec.api
        for spec in specs
        if len(match_urls(req.protocol.value, req.host, spec.api)) > 0
    }

    filtered = {k: _oai_modifier(v) for k, v in specs_with_matching_urls.items()}

    return [OpenAPISpecification(api, source) for (source, api) in filtered.items()]
