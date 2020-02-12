from meeshkan.gen.generator import match_urls, get_path_item_with_method
from openapi_typed import PathItem

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
