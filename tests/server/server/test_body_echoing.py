import pytest

from meeshkan.server import make_mocking_app
from meeshkan.server.utils.routing import PathRouting
from tornado.httpclient import AsyncHTTPClient, HTTPRequest


@pytest.fixture
def app():
    return make_mocking_app("tests/server/server/callbacks", "tests/server/mock/petstore_schema", PathRouting())


@pytest.mark.gen_test
def test_body_echoing(http_client: AsyncHTTPClient, base_url: str):
    req = HTTPRequest(
        url=base_url + "/http://petstore.swagger.io/v1/pets",
        method="POST",
        body="hello, world",
    )
    ret = yield http_client.fetch(req)
    assert ret.body.decode("utf-8") == "hello, world"
