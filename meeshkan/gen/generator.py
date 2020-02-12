from functools import reduce
import lenses
from lenses.optics.base import Prism
lens = lenses.lens
from typing import List, TypeVar, Callable, Optional, Dict, Union, Any
from openapi_typed import OpenAPIObject, Components, Reference, Schema, PathItem
from urllib.parse import urlparse

C = TypeVar('C') 
D = TypeVar('D')
S = TypeVar('S')
T = TypeVar('T')
W = TypeVar('W')
X = TypeVar('X')
Y = TypeVar('Y')
Z = TypeVar('Z')

all_methods: List[str] = [
  "get",
  "post",
  "put",
  "delete",
  "options",
  "head",
  "patch",
  "trace",
]

def omit(p: Dict[X, Y], a: X) -> Dict[X, Y]:
    return { k: v for k, v in p.items() if k != a}

# TODO are these types correct??
# C because I think the third thingee is the incoming type... maybe?
def odl(l: lenses.ui.BaseUiLens[S, T, X, Y], focus: str) -> lenses.ui.BaseUiLens[S, T, X, Y]:
    '''Short for "optional-dict-lens, equivalent of Opional in other optics libraries

    Arguments:
        l {lenses.ui.BaseUiLens[S, T, X, Y]} -- The incoming lens.
        focus {str} -- The key to focus on.
    
    Returns:
        D -- The thing we're focusing on
    '''
    return l.Iso(
        lambda a: (None if focus not in a else a[focus], a), lambda b: b[1]
    ).Prism(lambda a: a[0], lambda b: b, ignore_none = True)

def match_urls(protocol: str, host: str, o: OpenAPIObject) -> List[str]:
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

def get_component_from_ref(o: OpenAPIObject, d: str, accessor: Callable[[Components], Optional[Dict[str, Union[Reference, C]]]], getter: Callable[[OpenAPIObject, Union[C, Reference]], Optional[C]]) -> Optional[C]:
    return lens.F(
        lambda a: a['components'] if 'components' in a else None
    ).F(
        lambda a: a if a is None else accessor(a)
    ).F(
        lambda a: a if a is None else getter(o, a[d])
    ).get(o)

def is_reference(a: Any) -> bool:
    return '$ref' in a

def internal_get_component(f: Callable[[OpenAPIObject, str], Optional[C]]) -> Callable[[OpenAPIObject, Union[C,  Reference]], Optional[C]]:
    def _internal_get_component(o: OpenAPIObject, i: Union[C,  Reference]) -> Optional[C]:
        return (f(o, i['$ref'].split('/')[3]) if is_reference(i) else i) if i is not None else None
    return _internal_get_component

def get_schema_from_ref(o: OpenAPIObject, d: str) -> Optional[Schema]:
    return get_component_from_ref(o, d, lambda a: a['schemas'] if 'schemas' in a else None, internal_get_schema_from_ref)

internal_get_schema_from_ref = internal_get_component(get_schema_from_ref)

def schema_prism(oai: OpenAPIObject) -> Callable[[lenses.ui.BaseUiLens[S, T, X, Y]], lenses.ui.BaseUiLens[S, T, X, Y]]:
    def _schema_prism(l: lenses.ui.BaseUiLens[S, T, X, Y]) -> lenses.ui.BaseUiLens[S, T, X, Y]:
        return l.Prism(lambda s: get_schema_from_ref(oai, s['$ref'].split('/')[3]) if is_reference(s) else s, lambda a: a)
    return _schema_prism

def change_ref(j: Reference) -> Reference:
    return {
        '$ref': '#/definitions/%s' % j['$ref'].split("/")[3],
    }

def change_refs(j: Schema) -> Schema:
    return {
        **j,
        **({} if 'additionalProperties' not in j
            else { 'additionalProperties': change_ref(j['additionalProperties']) }
            if is_reference(j['additionalProperties'])
            else  { 'additionalProperties': {} }
            if type(j['additionalProperties']) == 'bool'
            else { 'additionalProperties': change_refs(j['additionalProperties']) }),
        **({} if 'items' not in j
            else { 'items': change_ref(j['items']) }
            if is_reference(j['items'])
            else {
                'items': [change_ref(item) if is_reference(item) else change_refs(item) for item in j['items']]
            } if type(j['items']) == type([])
            else { 'items': change_refs(j['items']) }),
        **({} if 'properties' not in j
            else {
                'properties': reduce(
                    lambda a, b: { **a, [b[0]]: change_ref(b[1]) if is_reference(b[1]) else change_refs(b[1]) },
                    j['properties'].items(),
                    {})
            })
    }

def make_definitions_from_schema(o: OpenAPIObject) -> Dict[str, Schema]:
  return reduce(lambda a, b: { **a, b[0]: change_ref(b[1]) if is_reference(b[1]) else change_refs(b[1]) }, o['components']['schemas'], {}) if ('components' in o) and ('schemas' in o['components']) else {}

def find_relevant_path(m: str, a: List[str], p: PathItem) -> PathItem:
  return p if len(a) == 0 else find_relevant_path(
        m,
        a[1:],
        p if a[0] == m else omit(p, a[0]),
      )


def get_path_item_with_method(m: str, p: PathItem) -> PathItem:
  return find_relevant_path(m, all_methods, p);