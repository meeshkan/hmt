from functools import reduce
import lenses
from lenses.optics.base import Prism
lens = lenses.lens
import jsonschema
import json
import re
from http_types import Request
from typing import cast, Sequence, Tuple, TypeVar, Callable, Optional, Mapping, Union, Any
from openapi_typed import OpenAPIObject, Response, RequestBody, Header, Operation, Parameter, Components, Reference, Schema, PathItem
from urllib.parse import urlparse

C = TypeVar('C') 
D = TypeVar('D')
S = TypeVar('S')
T = TypeVar('T')
W = TypeVar('W')
X = TypeVar('X')
Y = TypeVar('Y')
Z = TypeVar('Z')

__all__ = ['matcher', 'faker', 'change_ref', 'change_refs']


#def pp(s, c: C) -> C:
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

def omit(p: C, a: str) -> C:
    return { k: v for k, v in p.items() if k != a}

_prism_o = (lambda a: a, lambda b: b)

# TODO are these types correct??
# C because I think the third thingee is the incoming type... maybe?
def odl(focus: Union[str, int]) -> lenses.ui.BaseUiLens[S, T, X, Y]:
    '''Short for "optional-dict-lens, equivalent of Opional in other optics libraries

    Arguments:
        focus {str} -- The key to focus on.
    
    Returns:
        lenses.ui.BaseUiLens[S, T, X, Y] -- A lens that creates the equivalent of an optional
    '''
    return lens.Items().Filter(lambda a: a[0] == focus)[1]
    

def match_urls(protocol: str, host: str, o: OpenAPIObject) -> Sequence[str]:
    """Finds server URLs that match a given protocol and host.

    Arguments:
        protocol {str} -- like http or https
        host {str} -- like api.foo.com
        o {OpenAPIObject} -- schema from which the server URLs are taken
    
    Returns:
        A list of URLs that match the OpenAPI spec.
    """
    return [server['url']
        for server in o['servers']
        if (urlparse(server['url']).scheme == protocol)
            and  (urlparse(server['url']).netloc == host)] if 'servers' in o else []

def get_component_from_ref(o: OpenAPIObject, d: str, accessor: Callable[[Components], Optional[Mapping[str, Union[Reference, C]]]], getter: Callable[[OpenAPIObject, Union[C, Reference]], Optional[C]]) -> Optional[C]:
    return lens.F(
        lambda a: a['components'] if 'components' in a else None
    ).F(
        lambda a: a if a is None else accessor(a)
    ).F(
        lambda a: a if a is None else getter(o, a[d])
    ).get()(o)

def is_reference(a: Any) -> bool:
    return '$ref' in a

def ref_name(r: Reference) -> str:
    return r['$ref'].split("/")[3]

def internal_get_component(f: Callable[[OpenAPIObject, str], Optional[C]]) -> Callable[[OpenAPIObject, Union[C,  Reference]], Optional[C]]:
    def _internal_get_component(o: OpenAPIObject, i: Union[C,  Reference]) -> Optional[C]:
        return (f(o, ref_name(i)) if is_reference(i) else i) if i is not None else None
    return _internal_get_component

# TODO: it seems that there is a bug in pyright that makes get_component_from_ref return a Union[Reference, Schema] instead of Schema
# need to do a cast of the output value to Schema (instead of the union) to fix that
# same for functions below
def get_schema_from_ref(o: OpenAPIObject, d: str) -> Optional[Schema]:
    out = get_component_from_ref(o, d, lambda a: a['schemas'] if 'schemas' in a else None, internal_get_schema_from_ref)
    return None if out is None else cast(Schema, out)

internal_get_schema_from_ref = internal_get_component(get_schema_from_ref)

def get_parameter_from_ref(o: OpenAPIObject, d: str) -> Optional[Parameter]:
    out = get_component_from_ref(o, d, lambda a: a['parameters'] if 'parameters' in a else None, internal_get_parameter_from_ref)
    return None if out is None else cast(Parameter, out)

internal_get_parameter_from_ref = internal_get_component(get_parameter_from_ref)

def get_request_body_from_ref(o: OpenAPIObject, d: str) -> Optional[RequestBody]:
    out = get_component_from_ref(o, d, lambda a: a['requestBodies'] if 'requestBodies' in a else None, internal_get_request_body_from_ref)
    return None if out is None else cast(RequestBody, out)

internal_get_request_body_from_ref = internal_get_component(get_request_body_from_ref)

def get_response_from_ref(o: OpenAPIObject, d: str) -> Optional[Response]:
    out = get_component_from_ref(o, d, lambda a: a['responses'] if 'responses' in a else None, internal_get_response_from_ref)
    return None if out is None else cast(Response, out)

internal_get_response_from_ref = internal_get_component(get_response_from_ref)


def schema_prism(oai: OpenAPIObject) -> lenses.ui.BaseUiLens[S, T, X, Y]:
    return lens.Prism(
        lambda s: get_schema_from_ref(oai, ref_name(s)) if is_reference(s) else s,
        lambda a: a,
        ignore_none=True
    )

def change_ref(j: Reference) -> Reference:
    return {
        '$ref': '#/definitions/%s' % ref_name(j),
    }

def change_refs(j: Schema) -> Schema:
    return cast(Schema, {
        **j,
        **({} if 'additionalProperties' not in j
            else { 'additionalProperties': {} }
            if type(j['additionalProperties']) == type(True)
            else { 'additionalProperties': change_ref(cast(Reference, j['additionalProperties'])) }
            if is_reference(j['additionalProperties'])
            else  { 'additionalProperties': {} }
            if type(j['additionalProperties']) == 'bool'
            else { 'additionalProperties': change_refs(cast(Schema, j['additionalProperties'])) }),
        **({} if 'items' not in j
            else { 'items': change_ref(cast(Reference, j['items'])) }
            if is_reference(j['items'])
            else {
                'items': [change_ref(cast(Reference, item)) if is_reference(item) else change_refs(cast(Schema, item)) for item in cast(Sequence, j['items'])]
            } if type(j['items']) == type([])
            else { 'items': change_refs(cast(Schema, j['items'])) }),
        **({} if 'properties' not in j
            else {
                'properties': { k: change_ref(cast(Reference, v)) if is_reference(v) else change_refs(cast(Schema, v)) for k, v in j['properties'].items() }
            }),
        **(reduce(
            lambda a, b: { **a, **b },
            [{} if x not in j else { x: [change_ref(cast(Reference, y)) if is_reference(y) else change_refs(cast(Schema, y)) for y in j[x]] } for x in ['anyOf', 'allOf', 'oneOf']],
            {}))
    })

def make_definitions_from_schema(o: OpenAPIObject) -> Mapping[str, Schema]:
    return {
        # TODO: should the second cast be to Union[Schema, Reference]? In unmock it is just Schema, but perhaps it should be both...
        cast(str, a): cast(Schema, change_ref(cast(Reference, b)) if is_reference(b) else change_refs(cast(Schema, b))) for a, b in o['components']['schemas'].items()
    } if ('components' in o) and ('schemas' in o['components']) else {}

def find_relevant_path(m: str, a: Sequence[str], p: PathItem) -> PathItem:
  return p if len(a) == 0 else find_relevant_path(
        m,
        a[1:],
        p if a[0] == m else omit(p, a[0]),
      )


def get_path_item_with_method(m: str, p: PathItem) -> PathItem:
    return find_relevant_path(m, all_methods, p)

def get_required_request_query_or_header_parameters_internal(header: bool, l: lenses.ui.BaseUiLens[S, T, X, Y], oai: OpenAPIObject, p: PathItem) -> Sequence[Parameter]:
    # TODO: really dirty cast
    # is this even the case
    # copied from unmock, but need to investigate
    return cast(Sequence[Parameter], [{ **parameter, 'schema': (change_ref(cast(Reference, parameter['schema'])) if is_reference(parameter['schema']) else change_refs(cast(Schema, parameter['schema']))) if 'schema' in parameter else cast(Schema, { 'type': "string" }) } for parameter in l.Prism(
        lambda s: get_parameter_from_ref(oai, ref_name(s)) if is_reference(s) else s,
        lambda a : a,
        ignore_none=True
    ).Prism(
        lambda s : s if (s['in'] == ( "header" if header else "query")) and ('required' in s) and s['required'] else None,
        lambda a : a,
        ignore_none=True
    ).collect()(p) if ('schema' in parameter) and (len(lens.Each().add_lens(schema_prism(oai)).collect()([parameter['schema']])) > 0)])

def get_required_request_query_or_header_parameters(header: bool, req: Request, oai: OpenAPIObject, p: PathItem) -> Sequence[Parameter]:
    return [
        *get_required_request_query_or_header_parameters_internal(
            header,
            odl("parameters").Each(),
            oai,
            p),
        *get_required_request_query_or_header_parameters_internal(
            header,
            odl(req['method'].lower()).add_lens(
                odl("parameters")
            ).Each(),
            oai,
            p)
    ]

def get_required_request_body_schemas(
  req: Request,
  oai: OpenAPIObject,
  p: PathItem,
) -> Sequence[Schema]:
    return odl(req['method'].lower()).add_lens(
        odl("requestBody")
    ).Prism(
        lambda s : get_request_body_from_ref(oai, ref_name(s)) if is_reference(s) else s,
        lambda a: a,
        ignore_none=True
    ).add_lens(
        odl("content")
    ).Values().add_lens(
        odl("schema")
    ).add_lens(schema_prism(oai)).collect()(p)

def valid_schema(to_validate: Any, schema: Any) -> bool:
    try:
        jsonschema.validate(to_validate, schema)
        return True
    except Exception as e:
        # print(e)
        return False

def keep_method_if_required_request_body_is_present(
    req: Request,
    oai: OpenAPIObject,
) -> Callable[[PathItem], PathItem]:
    def _keep_method_if_required_request_body_is_present(p: PathItem) -> PathItem:
        return p if (req['method'].lower() not in p) or (len([s for s in get_required_request_body_schemas(req, oai, p) if
                not valid_schema(req['bodyAsJson'], {
                    # TODO: this line is different than the TS implementation
                    # because I think there is a logic bug there
                    # it should look like this line as we are not sure
                    # if the schema will be a reference or not
                    # perhaps I'm wrong in the assumption... only testing will tell...
                    # otherwise, change the TS implementation in unmock-js and delete this comment.
                    **(change_ref(cast(Reference, s)) if is_reference(s) else change_refs(cast(Schema, s))),
                    'definitions': make_definitions_from_schema(oai),
                })]) == 0) else omit(p, req['method'].lower())
    return _keep_method_if_required_request_body_is_present

def keep_method_if_required_header_parameters_are_present(
    req: Request,
    oai: OpenAPIObject,
) -> Callable[[PathItem], PathItem]:
    def _keep_method_if_required_header_parameters_are_present(p: PathItem) -> PathItem:
        return keep_method_if_required_query_or_header_parameters_are_present(True, req, oai, p)
    return _keep_method_if_required_header_parameters_are_present

def keep_method_if_required_query_parameters_are_present(
    req: Request,
    oai: OpenAPIObject,
) -> Callable[[PathItem], PathItem]:
    def _keep_method_if_required_query_parameters_are_present(p: PathItem) -> PathItem:
        return keep_method_if_required_query_or_header_parameters_are_present(False, req, oai, p)
    return _keep_method_if_required_query_parameters_are_present

def _json_schema_from_required_parameters(parameters: Sequence[Parameter], oai: OpenAPIObject) -> Any:
    return {
        'type': 'object',
        'properties': {param['name']: param['schema'] for param in parameters},
        'required': [param['name'] for param in parameters if ('required' in param) and param['required']],
        'additionalProperties': True,
        'definitions': make_definitions_from_schema(oai),
    }


def keep_method_if_required_query_or_header_parameters_are_present(
    header: bool,
    req: Request,
    oai: OpenAPIObject,
    p: PathItem
) -> PathItem:
    return p if (req['method'].lower() not in p) or valid_schema(
        req['headers'] if header else req['query'],
        _json_schema_from_required_parameters(get_required_request_query_or_header_parameters(header, req, oai, p), oai)
    ) else omit(p, req['method'].lower())

def maybe_add_string_schema(s: Sequence[Union[Reference, Schema]]) -> Sequence[Union[Reference, Schema]]:
    return [cast(Schema, { 'type': "string" })] if len(s) == 0 else s

def discern_name(o: Optional[Parameter], n: str) -> Optional[Parameter]:
    return o if (o is None) or ((o['name'] == n) and (o['in'] == 'path')) else None

def internal_get_parameter_schemas(
    t: lenses.ui.BaseUiLens[S, T, X, Y],
    vname: str,
    path_item: PathItem,
    oas: OpenAPIObject,
) -> Sequence[Schema]:
    return t.Prism(
        lambda i: discern_name(get_parameter_from_ref(oas, ref_name(i)), vname) if is_reference(i) else discern_name(i, vname),
        lambda a: a,
        ignore_none=True
    ).add_lens(
        odl("schema")
    ).collect()(path_item)


def path_item_path_parameter_schemas(
    vname: str,
    path_item: PathItem,
    oas: OpenAPIObject,
) -> Sequence[Schema]:
    return internal_get_parameter_schemas(
        odl('parameters').Each(),
        vname,
        path_item,
        oas,
    )

def operation_path_parameter_schemas(
  vname: str,
  path_item: PathItem,
  operation: str,
  oas: OpenAPIObject,
) -> Sequence[Schema]:
    return internal_get_parameter_schemas(
        odl(
            operation.lower()
        ).add_lens(
            odl('parameters')
        ).Each(),
        vname,
        path_item,
        oas,
  )

def get_matching_parameters(
  vname: str,
  path_item: PathItem,
  operation: str,
  oas: OpenAPIObject,
) -> Sequence[Union[Schema, Reference]]:
    return maybe_add_string_schema([
        *path_item_path_parameter_schemas(vname, path_item, oas),
        *operation_path_parameter_schemas(vname, path_item, operation, oas)
    ])

def maybeJson(maybe: str) -> Any:
  try:
    return json.loads(maybe)
  except:
    return maybe

def path_parameter_match(
    part: str,
    vname: str,
    path_item: PathItem,
    operation: str,
    oas: OpenAPIObject,
) -> bool:
    '''Matches part of a path against a path parameter with name vname
    
    Arguments:
        part {str} -- part of a path, ie an id
        vname {str} -- name of a parameter
        path_item {PathItem} -- a path item maybe containing the parameter
        operation {MethodNames} -- the name of the operation to check in case the parameter is in the operation
        oas {OpenAPIObject} -- the schema to traverse to find definitions
    
    Returns:
        bool -- Did we get a match
    '''
    return reduce(lambda q, r: q and reduce(
        lambda a, b:
          a or
          valid_schema(b, {
            **r,
            'definitions': make_definitions_from_schema(oas),
          }),
        list(set([part, maybeJson(part)])),
        False,
    ), get_matching_parameters(vname, path_item, operation, oas), True)

path_param_regex = re.compile(r'^\{[^}]+\}')

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
        (len(path) == 0) or
        (((path[0] == path_item_key[0]) or
        ((path_param_regex.match(path_item_key[0]) is not None) and
            path_parameter_match(
                path[0],
                path_item_key[0][1:-1],
                path_item,
                operation,
                o,
            ))) and
            matches_internal(
                path[1:],
                path_item_key[1:],
                path_item,
                operation,
                o,
            )))

def matches(
  path: str,
  path_item_key: str,
  path_item: PathItem,
  method: str,
  oas: OpenAPIObject,
) -> bool:
  return matches_internal(
    [x for x in path.split("/") if x != ""],
    [x for x in path_item_key.split("/") if x != ""],
    path_item,
    method,
    oas,
  )

def get_first_method_internal_2(
  p: PathItem,
  n: str,
  m: Sequence[str],
  o: Optional[Operation],
) ->  Optional[Tuple[str, Operation]]:
    return (n, o) if o is not None else get_first_method_internal(m, p)

def get_first_method_internal(
  m: Sequence[str],
  p: PathItem,
) -> Optional[Tuple[str, Operation]]:
    return None if len(m) == 0 else get_first_method_internal_2(p, m[0], m[1:], p[m[0]] if m[0] in p else None)

def get_first_method(p: PathItem) -> Optional[Tuple[str, Operation]]:
  return get_first_method_internal(all_methods, p)

def get_header_from_ref(
    o: OpenAPIObject,
    d: str
) -> Optional[Header]:
    out = get_component_from_ref(
        o,
        d,
        lambda a: a['headers'] if 'headers' in a else None,
        internal_get_header_from_ref,
    )
    return None if out is None else cast(Header, out)

internal_get_header_from_ref = internal_get_component(get_header_from_ref)

def use_if_header_last_mile(
  p: Parameter,
  r: Optional[Schema],
) -> Optional[Tuple[str, Schema]]:
  return None if r is None else (p['name'], r if r is not None else cast(Schema, { 'type': "string" }))

def use_if_header(
  o: OpenAPIObject,
  p: Parameter,
) -> Optional[Tuple[str, Schema]]:
    return None if p['in'] != "header" else use_if_header_last_mile(
        p,
        cast(Schema, { 'type': "string" }) if ('schema' not in p) or (p['schema'] is None) else
            get_schema_from_ref(o, ref_name(cast(Reference, p['schema']))) if is_reference(p['schema']) else
                cast(Schema, p['schema'])
    )

def parameter_schema(o: OpenAPIObject) -> lenses.ui.BaseUiLens[S, T, X, Y]:
    return lens.Iso(lambda a: (use_if_header(o, a), a), lambda b: b[1])[0].Prism(*_prism_o, ignore_none=True)


def cut_path(paths: Sequence[str], path: str) -> str:
    return path if len(paths) == 0 else path[len(paths[0]):] if path[:len(paths[0])] == paths[0] else cut_path(paths[1:], path)

def remove_trailing_slash(s: str) -> str:
    return s if len(s) == 0 else s[:-1] if s[-1] == "/" else s

def truncate_path(
  path: str,
  o: OpenAPIObject,
  i: Request,
) -> str:
    return cut_path(
        [remove_trailing_slash(urlparse(u).path) for u in match_urls(i['protocol'], i['host'], o)],
        path,
    )

def matcher(req: Request, r: Mapping[str, OpenAPIObject]) -> Mapping[str, OpenAPIObject]:
    return lens.Values().modify(
        lambda oai: odl("paths").Values().modify(
            lambda path_item: reduce(lambda a, b: b(a), [
                keep_method_if_required_header_parameters_are_present(req, oai),
                keep_method_if_required_query_parameters_are_present(req, oai),
                keep_method_if_required_request_body_is_present(req, oai),
            ], get_path_item_with_method(req['method'].lower(), path_item))
        )({
            **oai,
            **({} if 'paths' not in oai else {
              'paths': {n: o for n, o in oai['paths'].items() if matches(
                    truncate_path(req['pathname'], oai, req),
                    n,
                    o,
                    req['method'].lower(),
                    oai,
                  )}
                })
        })
    )({k: v for k, v in r.items() if len(match_urls(req['protocol'], req['host'], v)) > 0 })

def _first_or_none(l: Sequence[C]) -> Optional[C]:
    return None if len(l) == 0 else l[0]

def is_parameter(s: Any) -> bool:
    return s is not None and 'in' in s and 'name' in s

def headers_schemas_from_operation(schema: OpenAPIObject, operation: Operation) -> Sequence[Schema]:
    return odl("parameters").Each().Prism(
        lambda s: s if is_parameter(s) else get_parameter_from_ref(schema, ref_name(s)) if is_reference(s) else None,
        lambda a: a,
        ignore_none=True
    ).Iso(
        lambda a: (use_if_header(schema, a), a),
        lambda b: b[1]
    )[0].Prism(*_prism_o, ignore_none=True).collect()(operation)

# TODO: this is pretty impovrished compared to unmock JS
# can we make it better
def is_response(a: Any) -> bool:
    return (a is not None) and ('description' in a) and (True if 'content' not in a else type(a['content']) == type({}))

def make_lens_to_response_starting_from_operation(
    schema: OpenAPIObject,
    code: str,
    l: lenses.ui.BaseUiLens[S, T, X, Y] = lens
) -> lenses.ui.BaseUiLens[S, T, X, Y]:
    return l.add_lens(odl("responses")).Prism(
        lambda s: s if is_response(s) else 
            get_response_from_ref(schema, ref_name(s)) if is_reference(s) else
            None,
        lambda a: a,
        ignore_none=True
    )

def string_header(n: str, o: Optional[Header]) -> Optional[Tuple[str, Header]]:
    return None if o is None else (n, o)

def header_schemas_from_response(
  schema: OpenAPIObject,
  operation: Operation,
  code: str
) -> Sequence[Schema]:
    return make_lens_to_response_starting_from_operation(
      schema, code
    ).add_lens(odl("headers")).Items().Prism(
      lambda a: string_header(a[0], get_header_from_ref(schema, ref_name(a[1]))) if is_reference(a[1]) else (a[0], a[1]),
      lambda a: a,
      ignore_none=True
    ).Iso(
      lambda a: { **a[1], 'name': a[0], 'in': 'header' },
      lambda a: (a['name'], a)
    ).add_lens(parameter_schema(schema)).collect()(operation)

def body_from_response(
  schema: OpenAPIObject,
  operation: Operation,
  code: str
) -> Optional[Union[Reference, Schema]]:
  return _first_or_none(
    make_lens_to_response_starting_from_operation(
          schema, code
    ).add_lens(
        odl("content")
    ).Items().add_lens(
        odl(0)
    )[1].add_lens(
        odl("schema")
    ).collect()([operation]))


########################
#### FAKER
########################
import random
from faker import Faker
fkr = Faker()
_LO = -99999999
_HI = 99999999

# to prevent too-nested objects
def sane_depth(n):
    return max([0, 3-n])

def fake_object(schema: Any, top_schema: Any, depth: int) -> Any:
    addls = {} if 'additionalProperties' not in schema else {k:v for k,v in [(fkr.name(), random.random() if (type(schema['additionalProperties']) == type(True)) and (schema['additionalProperties'] == True) else faker(schema['additionalProperties'], top_schema, depth)) for x in range(random.randint(0, 4))]}
    properties = [] if 'properties' not in schema else [x for x in schema['properties'].keys()]
    random.shuffle(properties)
    properties = [] if len(properties) == 0 else properties[:min([sane_depth(depth), random.randint(0, len(properties) - 1 )])]
    properties = list(set(([] if 'required' not in schema else schema['required']) + properties))
    return {
        **addls,
        **{ k: v for k,v in [(p, faker(schema['properties'][p], top_schema, depth)) for p in properties]}
    }

def fake_array(schema: Any, top_schema: Any, depth: int) -> Any:
    mn = 0 if 'minItems' not in schema else schema['minItems']
    mx = 100 if 'maxItems' not in schema else schema['maxItems']
    return [faker(x, top_schema, depth) for x in schema['items']] if type(schema['items']) is type([]) else [faker(schema['items'], top_schema, depth) for x in range(random.randint(mn, mx))]

def fake_any_of(schema: Any, top_schema: Any, depth: int) -> Any:
    return faker(random.choice(schema["anyOf"]), top_schema, depth)

def fake_all_of(schema: Any, top_schema: Any, depth: int) -> Any:
    return reduce(lambda a, b: { **a, **b}, [faker(x, top_schema, depth) for x in schema["allOf"]], {})

def fake_one_of(schema: Any, top_schema: Any, depth: int) -> Any:
    return faker(random.choice(schema["oneOf"]), top_schema, depth)

# TODO - make this work
def fake_not(schema: Any, top_schema: Any, depth: int) -> Any:
    return {}

# TODO - make this not suck
def fake_string(schema: Any) -> str:
    return random.choice(schema['enum']) if 'enum' in schema else fkr.name()

def fake_boolean(schema: Any) -> bool:
    return True if random.random() > 0.5 else False

# TODO: add exclusiveMinimum and exclusiveMaximum
def fake_integer(schema: Any) -> int:
    mn = _LO if 'minimum' not in schema else schema['minimum']
    mx = _HI if 'maximum' not in schema else schema['maximum']
    return random.choice(schema['enum']) if 'enum' in schema else random.randint(mn, mx)

def fake_ref(schema: Any, top_schema, depth):
    name = schema['$ref'].split('/')[2]
    return faker(top_schema['definitions'][name], top_schema, depth)

def fake_null(schema: Any) -> None:
    return None

def fake_number(schema: Any) -> float:
    mn = _LO if 'minimum' not in schema else schema['minimum']
    mx = _HI if 'maximum' not in schema else schema['maximum']
    return random.choice(schema['enum']) if 'enum' in schema else (random.random() * (mx - mn)) + mn

def faker(schema: Any, top_schema: Any, depth: int) -> Any:
    depth += 1
    return fake_array(
        schema, top_schema, depth
    ) if ('type' in schema) and (schema["type"] == "array") else fake_any_of(
        schema, top_schema, depth
    ) if "anyOf" in schema else fake_all_of(
        schema, top_schema, depth
    ) if "allOf" in schema else fake_one_of(
        schema, top_schema, depth
    ) if "oneOf" in schema else fake_not(
        schema, top_schema, depth
    ) if "not" in schema else fake_ref(
        schema, top_schema, depth
    ) if "$ref" in schema else fake_object(
        schema, top_schema, depth
    ) if ("type" not in schema) or (schema["type"] == "object") else fake_string(
        schema
    ) if schema["type"] == "string" else fake_integer(
        schema
    ) if schema["type"] == "integer" else fake_boolean(
        schema
    ) if schema["type"] == "boolean" else fake_null(
        schema
    ) if schema["type"] == "null" else fake_number(
        schema
    ) if schema["type"] == "number" else {}