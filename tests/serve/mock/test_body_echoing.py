import pytest
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from meeshkan.serve.mock.log import Log
from meeshkan.serve.mock.scope import Scope
from meeshkan.serve.mock.server import make_mocking_app
from meeshkan.serve.mock.specs import load_specs
from meeshkan.serve.utils.routing import PathRouting


@pytest.fixture
def app():
    return make_mocking_app(
        "tests/serve/mock/callbacks",
        load_specs("tests/serve/mock/schemas/petstore"),
        PathRouting(),
        Log(Scope()),
    )


@pytest.mark.gen_test
def test_body_echoing(http_client: AsyncHTTPClient, base_url: str):
    req = HTTPRequest(
        url=base_url + "/http://petstore.swagger.io/v1/pets",
        method="POST",
        body="hello, world",
    )
    ret = yield http_client.fetch(req)
    assert ret.body.decode("utf-8") == "hello, world"
