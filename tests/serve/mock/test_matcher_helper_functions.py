from dataclasses import replace

from openapi_typed_2 import (
    OpenAPIObject,
    PathItem,
    Reference,
    convert_to_Components,
    convert_to_openapi,
    convert_to_Parameter,
    convert_to_PathItem,
    convert_to_Schema,
)

from hmt.serve.mock.matcher import match_urls, matches
from hmt.serve.mock.refs import ref_name

# from hmt.serve.mock.request_validation import use_if_header


def test_match_urls():
    assert ["https://api.foo.com"] == match_urls(
        "https",
        "api.foo.com",
        convert_to_openapi(
            {
                "openapi": "",
                "paths": {},
                "info": {"title": "", "version": ""},
                "servers": [
                    {"url": "https://api.foo.commm/v2"},
                    {"url": "https://api.foo.com"},
                ],
            }
        ),
    )
    assert ["https://api.foo.com/v2/a/b/c"] == match_urls(
        "https",
        "api.foo.com",
        convert_to_openapi(
            {
                "openapi": "",
                "paths": {},
                "info": {"title": "", "version": ""},
                "servers": [
                    {"url": "https://api.foo.commm/v2"},
                    {"url": "https://api.foo.com/v2/a/b/c"},
                ],
            }
        ),
    )
    assert [] == match_urls(
        "https",
        "api.foo.com/v2",
        convert_to_openapi(
            {
                "openapi": "",
                "paths": {},
                "info": {"title": "", "version": ""},
                "servers": [
                    {"url": "https://api.foo.commm/v2"},
                    {"url": "https://api.foo.cooom/v2"},
                ],
            }
        ),
    )


def test_matcher():
    _bfoo = {
        "parameters": [
            {
                "in": "path",
                "name": "foo",
                "schema": {"type": "string", "pattern": "^[abc]+$"},
            },
        ],
        "get": {
            "responses": {
                "200": {"description": "some", "content": {"application/json": {}},}
            }
        },
    }
    bfoo = convert_to_PathItem(_bfoo)
    oai: OpenAPIObject = convert_to_openapi(
        {
            "openapi": "",
            "info": {"title": "", "version": ""},
            "paths": {"/b/{foo}": _bfoo},
        }
    )
    assert matches(["a", "b"], "/a/b", bfoo, "get")
    assert not matches(["a"], "/a/b", bfoo, "get")
    assert not matches(["a", "b"], "/a", bfoo, "get")
    assert matches(["a", "b", "c"], "/a/{fewfwef}/c", bfoo, "get")
    assert matches(["b", "ccaaca"], "/b/{foo}", bfoo, "get")
    assert matches(["b", "ccaaca"], "/b/{foo}", bfoo, "get")
    assert not matches(["a", "b", "c"], "/a/{fewfwef}/c", bfoo, "post")


def test_ref_name():
    assert "Foo" == ref_name(Reference(_ref="#/components/schemas/Foo", _x=None))


baseO: OpenAPIObject = convert_to_openapi(
    {
        "openapi": "hello",
        "info": {"title": "", "version": ""},
        "servers": [{"url": "https://hello.api.com"}],
        "paths": {},
    }
)


# def test_use_if_header():
#     assert (
#         use_if_header(baseO, convert_to_Parameter({"name": "foo", "in": "query"}))
#         is None
#     )
#     assert use_if_header(
#         baseO, convert_to_Parameter({"name": "foo", "in": "header"})
#     ) == ("foo", convert_to_Schema({"type": "string"}))
#     assert use_if_header(
#         baseO,
#         convert_to_Parameter(
#             {"name": "foo", "in": "header", "schema": {"type": "number"}}
#         ),
#     ) == ("foo", convert_to_Schema({"type": "number"}))
#     assert use_if_header(
#         replace(
#             baseO,
#             components=convert_to_Components({"schemas": {"Foo": {"type": "boolean"}}}),
#         ),
#         convert_to_Parameter(
#             {
#                 "name": "foo",
#                 "in": "header",
#                 "schema": {"$ref": "#/components/schemas/Foo"},
#             }
#         ),
#     ) == ("foo", convert_to_Schema({"type": "boolean"}))
