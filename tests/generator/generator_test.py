from meeshkan.gen.generator import match_urls, use_if_header, ref_name, get_path_item_with_method, matches
from openapi_typed import PathItem, OpenAPIObject

def test_match_urls():
    assert ["https://api.foo.com"] == match_urls("https", "api.foo.com", {
      "openapi": "",
      "paths": {},
      "info": { "title": "", "version": "" },
      "servers": [
        { "url": "https://api.foo.commm/v2" },
        { "url": "https://api.foo.com" },
      ],
    })
    assert ["https://api.foo.com/v2/a/b/c"] == match_urls("https", "api.foo.com", {
      "openapi": "",
      "paths": {},
      "info": { "title": "", "version": "" },
      "servers": [
        { "url": "https://api.foo.commm/v2" },
        { "url": "https://api.foo.com/v2/a/b/c" },
      ],
    })
    assert [] == match_urls("https", "api.foo.com/v2", {
      "openapi": "",
      "paths": {},
      "info": { "title": "", "version": "" },
      "servers": [
        { "url": "https://api.foo.commm/v2" },
        { "url": "https://api.foo.cooom/v2" },
      ],
    })

def test_get_path_item_with_method():
  o: PathItem = {
    'get': { 'responses': { '100': { 'description': "hello" } } },
    'post': { 'responses': { '101': { 'description': "hello" } } },
    'delete': { 'responses': { '102': { 'description': "hello" } } },
    'description': "foo",
  }
  assert get_path_item_with_method("get", o) == {
    'get': { 'responses': { '100': { 'description': "hello" } } },
    'description': "foo",
  }
  assert get_path_item_with_method("post", o) == {
    'post': { 'responses': { '101': { 'description': "hello" } } },
    'description': "foo",
  }

def test_matcher():
  bfoo = {
    'parameters': [
      {
        'in': "path",
        'name': "foo",
        'schema': { 'type': "string", 'pattern': "^[abc]+$" },
      },
    ],
  };
  oai: OpenAPIObject = {
    'openapi': "",
    'info': { 'title': "", 'version': "" },
    'paths': {
      "/b/{foo}": bfoo,
    },
  }
  assert matches("/a/b", "/a/b", bfoo, "get", oai)
  assert not matches("/a/", "/a/b", bfoo, "get", oai)
  assert not matches("/a/b", "/a", bfoo, "get", oai)
  assert matches("/a/b/c", "/a/{fewfwef}/c", bfoo, "get", oai)
  assert matches("/b/ccaaca", "/b/{foo}", bfoo, "get", oai)
  assert not matches("/b/ccaacda", "/b/{foo}", bfoo, "get", oai)

def test_ref_name():
  assert "Foo" == ref_name({ '$ref': "#/components/schemas/Foo" })

baseO: OpenAPIObject = {
  'openapi': "hello",
  'info': { 'title': "", 'version': "" },
  'servers': [{ 'url': "https://hello.api.com" }],
  'paths': {},
};

def test_use_if_header():
  assert use_if_header(baseO, { 'name': "foo", 'in': "query" }) is None
  assert use_if_header(baseO, { 'name': "foo", 'in': "header" }) == ("foo", { 'type': "string" })
  assert use_if_header(baseO, {
      'name': "foo",
      'in': "header",
      'schema': { 'type': "number" },
  }) == ("foo", { 'type': "number" })
  assert use_if_header(
      {
        **baseO,
        'components': { 'schemas': { 'Foo': { 'type': "boolean" } } },
      },
      {
        'name': "foo",
        'in': "header",
        'schema': { '$ref': "#/components/schemas/Foo" },
      },
    ) == ("foo", { 'type': "boolean" })
