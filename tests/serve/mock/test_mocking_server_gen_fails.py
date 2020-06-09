import pytest
from tornado.httpclient import HTTPClientError, HTTPRequest

from hmt.serve.mock.log import Log
from hmt.serve.mock.scope import Scope
from hmt.serve.mock.specs import load_specs
from hmt.serve.utils.routing import HeaderRouting


@pytest.fixture
def app(mocking_app, test_sink):
    return mocking_app(
        "tests/serve/mock/callbacks",
        load_specs("tests/serve/mock/schemas/fails"),
        HeaderRouting(),
        Log(Scope(), test_sink),
    )


2111


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
