import json
from typing import Sequence

from http_types import RequestBuilder
from openapi_typed_2 import convert_to_openapi

from meeshkan.serve.mock.matcher import match_request_to_openapi
from meeshkan.serve.mock.specs import OpenAPISpecification

store: Sequence[OpenAPISpecification] = [
    OpenAPISpecification(
        convert_to_openapi(
            {
                "openapi": "",
                "servers": [
                    {"url": "api.foo.com"}
                ],  # we omit the protocol and it should still match
                "info": {"title": "", "version": ""},
                "paths": {
                    "/user": {
                        "get": {"responses": {"200": {"description": "userget"}}},
                        "post": {"responses": {"200": {"description": "userpost"}}},
                        "description": "",
                    },
                    "/user/{id}": {
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"},
                            },
                        ],
                        "get": {"responses": {"200": {"description": "useridget"}}},
                        "post": {"responses": {"201": {"description": "useridpost"}}},
                    },
                    "/user/{id}/name": {
                        "get": {"responses": {"200": {"description": "useridnameget"}}},
                        "post": {
                            "responses": {"201": {"description": "useridnamepost"}}
                        },
                        "description": "",
                    },
                },
            }
        ),
        "foo",
    ),
    OpenAPISpecification(
        convert_to_openapi(
            {
                "openapi": "",
                "servers": [{"url": "https://api.bar.com/v1"}],
                "info": {"title": "", "version": ""},
                "paths": {
                    "/guest": {
                        "get": {"responses": {"200": {"description": "guestget"}}},
                        "post": {"responses": {"200": {"description": "guestpost"}}},
                        "description": "",
                    },
                    "/guest/{id}": {
                        "get": {"responses": {"200": {"description": "guestidget"}}},
                        "post": {"responses": {"201": {"description": "guestidpost"}}},
                        "description": "",
                    },
                    "/guest/{id}/name": {
                        "get": {
                            "responses": {"200": {"description": "guestidnameget"}}
                        },
                        "post": {
                            "responses": {"201": {"description": "guestidnamepost"}}
                        },
                        "description": "",
                    },
                },
            }
        ),
        "bar",
    ),
    OpenAPISpecification(
        convert_to_openapi(
            {
                "openapi": "",
                "servers": [{"url": "https://api.baz.com"}],
                "info": {"title": "", "version": ""},
                "paths": {
                    "/guest": {
                        "parameters": [
                            {
                                "in": "query",
                                "required": True,
                                "name": "hello",
                                "schema": {"type": "string", "pattern": "^[0-9]+$"},
                            },
                        ],
                        "get": {"responses": {"200": {"description": "guestget"}}},
                        "post": {
                            "parameters": [
                                {
                                    "in": "query",
                                    "required": True,
                                    "name": "thinking",
                                    "schema": {"type": "string"},
                                },
                            ],
                            "responses": {"200": {"description": "guestpost"}},
                        },
                        "description": "",
                    },
                    "/guest/{id}": {
                        "parameters": [
                            {
                                "in": "query",
                                "required": True,
                                "name": "a",
                                "schema": {"type": "string"},
                            },
                            {
                                "in": "query",
                                "required": True,
                                "name": "b",
                                "schema": {"type": "string"},
                            },
                            {"in": "query", "name": "c", "schema": {"type": "string"}},
                        ],
                        "get": {"responses": {"200": {"description": "guestidget"}}},
                        "post": {
                            "parameters": [
                                {
                                    "in": "header",
                                    "required": True,
                                    "name": "zz",
                                    "schema": {"type": "string"},
                                },
                                {
                                    "in": "query",
                                    "required": True,
                                    "name": "zzz",
                                    "schema": {"type": "string"},
                                },
                                {
                                    "in": "query",
                                    "name": "c",
                                    "schema": {"type": "string"},
                                },
                            ],
                            "responses": {"201": {"description": "guestidpost"}},
                        },
                        "description": "",
                    },
                    "/guest/{id}/name": {
                        "get": {
                            "responses": {"200": {"description": "guestidnameget"}}
                        },
                        "post": {
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["age"],
                                            "properties": {"age": {"type": "integer"}},
                                        },
                                    },
                                },
                            },
                            "responses": {"201": {"description": "guestidnamepost"}},
                        },
                        "description": "",
                    },
                },
            }
        ),
        "baz",
    ),
]


def test_matcher_1():
    assert match_request_to_openapi(
        RequestBuilder.from_dict(
            {
                "headers": {},
                "host": "api.foo.com",
                "path": "/user",
                "pathname": "/user",
                "protocol": "https",
                "method": "get",
                "query": {},
            }
        ),
        store,
    ) == [
        OpenAPISpecification(
            convert_to_openapi(
                {
                    "openapi": "",
                    "servers": [{"url": "api.foo.com"}],
                    "info": {"title": "", "version": ""},
                    "paths": {
                        "/user": {
                            "get": {"responses": {"200": {"description": "userget"}}},
                            "description": "",
                        },
                    },
                }
            ),
            "foo",
        )
    ]


def test_matcher_2():
    match_request_to_openapi(
        RequestBuilder.from_dict(
            {
                "headers": {},
                "host": "api.bar.com",
                "path": "/v1/guest/{id}",
                "pathname": "/v1/guest/{id}",
                "protocol": "https",
                "method": "post",
                "query": {},
            }
        ),
        store,
    ) == {
        "bar": convert_to_openapi(
            {
                "openapi": "",
                "servers": [{"url": "https://api.bar.com/v1"}],
                "info": {"title": "", "version": ""},
                "paths": {
                    "/guest/{id}": {
                        "post": {"responses": {"201": {"description": "guestidpost"}}},
                        "description": "",
                    },
                },
            }
        )
    }


def test_matcher_3():
    assert match_request_to_openapi(
        RequestBuilder.from_dict(
            {
                "headers": {},
                "host": "api.foo.com",
                "path": "/users",  # incorrect, should be user
                "pathname": "/users",  # incorrect, should be user
                "protocol": "https",
                "method": "get",
                "query": {},
            }
        ),
        store,
    ) == [
        OpenAPISpecification(
            convert_to_openapi(
                {
                    "openapi": "",
                    "servers": [{"url": "api.foo.com"}],
                    "info": {"title": "", "version": ""},
                    "paths": {},
                }
            ),
            "foo",
        )
    ]


def test_matcher_4():
    assert match_request_to_openapi(
        RequestBuilder.from_dict(
            {
                "headers": {},
                "host": "api.foo.com",
                "path": "/user/55",  # correctly parses number
                "pathname": "/user/55",  # correcly parses number
                "protocol": "https",
                "method": "get",
                "query": {},
            }
        ),
        store,
    ) == [
        OpenAPISpecification(
            convert_to_openapi(
                {
                    "openapi": "",
                    "servers": [{"url": "api.foo.com"}],
                    "info": {"title": "", "version": ""},
                    "paths": {
                        "/user/{id}": {
                            "parameters": [
                                {
                                    "name": "id",
                                    "in": "path",
                                    "required": True,
                                    "schema": {"type": "integer"},
                                },
                            ],
                            "get": {"responses": {"200": {"description": "useridget"}}},
                        },
                    },
                }
            ),
            "foo",
        ),
    ]


def test_matcher_5():
    assert match_request_to_openapi(
        RequestBuilder.from_dict(
            {
                "headers": {},
                "host": "api.foo.com",
                "path": "/user/fdsfsfwef",  # correctly rejects non-number
                "pathname": "/user/fdsfsfwef",  # correcly rejects non-number
                "protocol": "https",
                "method": "get",
                "query": {},
            }
        ),
        store,
    ) == [
        OpenAPISpecification(
            convert_to_openapi(
                {
                    "openapi": "",
                    "servers": [{"url": "api.foo.com"}],
                    "info": {"title": "", "version": ""},
                    "paths": {},
                }
            ),
            "foo",
        )
    ]


def test_matcher_6():
    assert match_request_to_openapi(
        RequestBuilder.from_dict(
            {
                "headers": {},
                "host": "api.foo.com",
                "path": "/user",
                "pathname": "/user",
                "protocol": "https",
                "method": "delete",  # does not exist
                "query": {},
            }
        ),
        store,
    ) == [
        OpenAPISpecification(
            convert_to_openapi(
                {
                    "openapi": "",
                    "servers": [{"url": "api.foo.com"}],
                    "info": {"title": "", "version": ""},
                    "paths": {"/user": {"description": ""}},
                }
            ),
            "foo",
        )
    ]


def test_matcher_7():
    assert (
        match_request_to_openapi(
            RequestBuilder.from_dict(
                {
                    "headers": {},
                    "host": "api.foo.commmm",  # does not exist
                    "path": "/user",
                    "pathname": "/user",
                    "protocol": "https",
                    "method": "get",
                    "query": {},
                }
            ),
            store,
        )
        == []
    )


def test_matcher_8():
    (baz_spec,) = (spec for spec in store if spec.source == "baz")
    (matched_spec,) = (
        spec
        for spec in match_request_to_openapi(
            RequestBuilder.from_dict(
                {
                    "headers": {},
                    "host": "api.baz.com",
                    "path": "/guest",
                    "pathname": "/guest",
                    "protocol": "https",
                    "method": "get",
                    "query": {"hello": "0"},  # query param must be integer
                }
            ),
            store,
        )
        if spec.source == "baz"
    )
    assert matched_spec.api.paths["/guest"].get == baz_spec.api.paths["/guest"].get


def test_matcher_9():
    (matched_spec,) = (
        spec
        for spec in match_request_to_openapi(
            RequestBuilder.from_dict(
                {
                    "headers": {},
                    "host": "api.baz.com",
                    "path": "/guest",
                    "pathname": "/guest",
                    "protocol": "https",
                    "method": "get",
                    "query": {"hello": "b"},  # query param intentionally off as string
                }
            ),
            store,
        )
        if spec.source == "baz"
    )
    assert matched_spec.api.paths["/guest"].get is None


def test_matcher_10():
    assert (
        match_request_to_openapi(
            RequestBuilder.from_dict(
                {
                    "headers": {},
                    "host": "api.baz.com",
                    "path": "/guest",
                    "pathname": "/guest",
                    "protocol": "https",
                    "method": "get",
                    "query": {},  # as query is required, this should fail
                }
            ),
            store,
        )[0]
        .api.paths["/guest"]
        .get
        is None
    )


def test_matcher_11():
    (baz_spec,) = (spec for spec in store if spec.source == "baz")
    (matched_spec,) = (
        spec
        for spec in match_request_to_openapi(
            RequestBuilder.from_dict(
                {
                    "headers": {},
                    "host": "api.baz.com",
                    "path": "/guest/3/name",
                    "pathname": "/guest/3/name",
                    "protocol": "https",
                    "method": "post",
                    "query": {},
                    "bodyAsJson": {"age": 42},
                    "body": json.dumps({"age": 42}),
                }
            ),
            store,
        )
        if spec.source == "baz"
    )
    assert (
        matched_spec.api.paths["/guest/{id}/name"].post
        == baz_spec.api.paths["/guest/{id}/name"].post
    )


def test_matcher_12():
    assert (
        match_request_to_openapi(
            RequestBuilder.from_dict(
                {
                    "headers": {},
                    "host": "api.baz.com",
                    "path": "/guest/3/name",
                    "pathname": "/guest/3/name",
                    "protocol": "https",
                    "method": "post",
                    "query": {},
                    "body": json.dumps({"age": "42"}),
                    "bodyAsJson": {"age": "42"},  # wrong type, as 42 is string
                }
            ),
            store,
        )[0]
        .api.paths["/guest/{id}/name"]
        .post
        is None
    )


def test_matcher_13():
    (baz_spec,) = (spec for spec in store if spec.source == "baz")
    (matched_spec,) = (
        spec
        for spec in match_request_to_openapi(
            RequestBuilder.from_dict(
                {
                    "headers": {"zz": "top"},
                    "host": "api.baz.com",
                    "path": "/guest/4",
                    "pathname": "/guest/4",
                    "protocol": "https",
                    "method": "post",
                    "query": {"zzz": "aaa", "a": "foo", "b": "baz"},
                }
            ),
            store,
        )
        if spec.source == "baz"
    )
    assert (
        matched_spec.api.paths["/guest/{id}"].post
        == baz_spec.api.paths["/guest/{id}"].post
    )


def test_matcher_14():
    assert (
        match_request_to_openapi(
            RequestBuilder.from_dict(
                {
                    "headers": {},  # no header will lead to undefined
                    "host": "api.baz.com",
                    "path": "/guest/4",
                    "pathname": "/guest/4",
                    "protocol": "https",
                    "method": "post",
                    "query": {"zzz": "aaa", "a": "foo", "b": "baz"},
                }
            ),
            store,
        )[0]
        .api.paths["/guest/{id}"]
        .post
        is None
    )


def test_matcher_15():
    match_request_to_openapi(
        RequestBuilder.from_dict(
            {
                "headers": {"X-Meeshkan-Scheme": "https", "Host": "api.bar.com"},
                "host": "api.bar.com",
                "path": "/v1/guest/{id}",
                "pathname": "/v1/guest/{id}",
                "protocol": "http",
                "method": "post",
                "query": {},
            }
        ),
        store,
    ) == [
        OpenAPISpecification(
            convert_to_openapi(
                {
                    "openapi": "",
                    "servers": [{"url": "https://api.bar.com/v1"}],
                    "info": {"title": "", "version": ""},
                    "paths": {
                        "/guest/{id}": {
                            "post": {
                                "responses": {"201": {"description": "guestidpost"}}
                            },
                            "description": "",
                        },
                    },
                }
            ),
            "baz",
        )
    ]
