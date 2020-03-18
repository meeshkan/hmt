import pytest
from tornado.httpclient import HTTPClientError, HTTPRequest

from meeshkan.serve.mock.log import AbstractSink, Log
from meeshkan.serve.mock.scope import Scope
from meeshkan.serve.mock.server import make_mocking_app
from meeshkan.serve.mock.specs import load_specs
from meeshkan.serve.utils.routing import HeaderRouting


class MockSink(AbstractSink):
    def __init__(self):
        self.interactions = []

    def write(self, interactions):
        self.interactions = interactions


@pytest.fixture
def test_sink():
    return MockSink()


@pytest.fixture
def app(test_sink):
    return make_mocking_app(
        "tests/serve/mock/callbacks",
        load_specs("tests/serve/mock/schemas/fails"),
        HeaderRouting(),
        Log(Scope(), test_sink),
    )


@pytest.mark.gen_test
def test_mocking_server_pets(http_client, base_url, test_sink):
    req = HTTPRequest(base_url + "/", headers={"Host": "bad.api.io"})
    try:
        yield http_client.fetch(req)
        assert False  # what's a good way to do this?
    except HTTPClientError as e:
        assert str(e) == "HTTP 400: Bad Request"


@pytest.mark.gen_test
def test_mocking_server_pets_bad_path(http_client, base_url, test_sink):
    req = HTTPRequest(base_url + "/fewewsdfeaf", headers={"Host": "bad.api.io"})
    try:
        yield http_client.fetch(req)
        assert False  # what's a good way to do this?
    except HTTPClientError as e:
        assert str(e) == "HTTP 501: Not Implemented"
