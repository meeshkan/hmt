import json

import pytest
import requests_mock
from tornado.httpclient import HTTPRequest

from meeshkan.serve.mock.log import Log
from meeshkan.serve.mock.rest import rest_middleware_manager
from meeshkan.serve.mock.scope import Scope
from meeshkan.serve.mock.server import make_mocking_app
from meeshkan.serve.mock.specs import load_specs
from meeshkan.serve.utils.routing import HeaderRouting


@pytest.fixture
def app():
    return make_mocking_app(
        "tests/serve/mock/callbacks",
        load_specs("tests/serve/mock/schemas/petstore"),
        HeaderRouting(),
        Log(Scope()),
    )


@pytest.fixture(autouse=True)
def setup():
    rest_middleware_manager.add("https://api.hello.world")
    yield True
    rest_middleware_manager.clear("https://api.hello.world")


@pytest.mark.gen_test
def test_rest_middleware(http_client, base_url, app):
    req = HTTPRequest(base_url + "/pets", headers={"Host": "petstore.swagger.io"})
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.hello.world",
            json={
                "petstore": {
                    "openapi": "3.0",
                    "info": {"title": "hello", "version": "world"},
                    "servers": [{"url": "http://petstore.swagger.io"}],
                    "paths": {
                        "/pets": {
                            "get": {
                                "responses": {
                                    "200": {
                                        "description": "a response",
                                        "content": {
                                            "application/json": {
                                                "schema": {
                                                    "type": "number",
                                                    "enum": [42],
                                                }
                                            }
                                        },
                                    }
                                }
                            }
                        }
                    },
                }
            },
        )
        response = yield http_client.fetch(req)
        assert 42 == json.loads(response.body)
