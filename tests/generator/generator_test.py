from meeshkan.gen.generator import match_urls, use_if_header, ref_name, get_path_item_with_method, matches
from openapi_typed_2 import PathItem, Reference, OpenAPIObject, convert_to_Parameter, convert_to_PathItem, convert_to_Components, convert_to_openapi, convert_to_Schema
from dataclasses import replace

def test_match_urls():
    assert ["https://api.foo.com"] == match_urls("https", "api.foo.com", convert_to_openapi({
      "openapi": "",
      "paths": {},
      "info": { "title": "", "version": "" },
      "servers": [
        { "url": "https://api.foo.commm/v2" },
        { "url": "https://api.foo.com" },
      ],
    }))
    assert ["https://api.foo.com/v2/a/b/c"] == match_urls("https", "api.foo.com", convert_to_openapi({
      "openapi": "",
      "paths": {},
      "info": { "title": "", "version": "" },
      "servers": [
        { "url": "https://api.foo.commm/v2" },
        { "url": "https://api.foo.com/v2/a/b/c" },
      ],
    }))
    assert [] == match_urls("https", "api.foo.com/v2", convert_to_openapi({
      "openapi": "",
      "paths": {},
      "info": { "title": "", "version": "" },
      "servers": [
        { "url": "https://api.foo.commm/v2" },
        { "url": "https://api.foo.cooom/v2" },
      ],
    }))

def test_get_path_item_with_method():
  o: PathItem = convert_to_PathItem({
    'get': { 'responses': { '100': { 'description': "hello" } } },
    'post': { 'responses': { '101': { 'description': "hello" } } },
    'delete': { 'responses': { '102': { 'description': "hello" } } },
    'description': "foo",
  })
  assert get_path_item_with_method("get", o) == convert_to_PathItem({
    'get': { 'responses': { '100': { 'description': "hello" } } },
    'description': "foo",
  })
  assert get_path_item_with_method("post", o) == convert_to_PathItem({
    'post': { 'responses': { '101': { 'description': "hello" } } },
    'description': "foo",
  })

def test_matcher():
  _bfoo = {
    'parameters': [
      {
        'in': "path",
        'name': "foo",
        'schema': { 'type': "string", 'pattern': "^[abc]+$" },
      },
    ],
  }
  bfoo = convert_to_PathItem(_bfoo)
  oai: OpenAPIObject = convert_to_openapi({
    'openapi': "",
    'info': { 'title': "", 'version': "" },
    'paths': {
      "/b/{foo}": _bfoo,
    },
  })
  assert matches("/a/b", "/a/b", bfoo, "get", oai)
  assert not matches("/a/", "/a/b", bfoo, "get", oai)
  assert not matches("/a/b", "/a", bfoo, "get", oai)
  assert matches("/a/b/c", "/a/{fewfwef}/c", bfoo, "get", oai)
  assert matches("/b/ccaaca", "/b/{foo}", bfoo, "get", oai)
  assert not matches("/b/ccaacda", "/b/{foo}", bfoo, "get", oai)

def test_ref_name():
  assert "Foo" == ref_name(Reference(_ref="#/components/schemas/Foo", _x=None))

baseO: OpenAPIObject = convert_to_openapi({
  'openapi': "hello",
  'info': { 'title': "", 'version': "" },
  'servers': [{ 'url': "https://hello.api.com" }],
  'paths': {},
});

def test_use_if_header():
  assert use_if_header(baseO, convert_to_Parameter({ 'name': "foo", 'in': "query" })) is None
  assert use_if_header(baseO, convert_to_Parameter({ 'name': "foo", 'in': "header" })) == ("foo", convert_to_Schema({ 'type': "string" }))
  assert use_if_header(baseO, convert_to_Parameter({
      'name': "foo",
      'in': "header",
      'schema': { 'type': "number" },
  })) == ("foo", convert_to_Schema({ 'type': "number" }))
  assert use_if_header(
      replace(baseO,
        components=convert_to_Components({'schemas': { 'Foo': { 'type': "boolean" }}}),
      ),
      convert_to_Parameter({
        'name': "foo",
        'in': "header",
        'schema': { '$ref': "#/components/schemas/Foo" },
      }),
    ) == ("foo", convert_to_Schema({ 'type': "boolean" }))
