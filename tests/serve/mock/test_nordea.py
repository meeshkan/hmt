import json
import logging

import pytest
from tornado.httpclient import HTTPRequest
from hamcrest import assert_that, has_key

from meeshkan.serve.mock.server import make_mocking_app
from meeshkan.serve.utils.routing import HeaderRouting

logging.basicConfig(level="DEBUG")

routing_headers = {"Host": "api.nordeaopenbanking.com", "X-Meeshkan-Scheme": "https"}


@pytest.fixture
def app():
    return make_mocking_app(
        "tests/serve/mock/callbacks", "tests/serve/mock/schemas/nordea", HeaderRouting()
    )


@pytest.mark.gen_test
def test_nordea_accounts_returns_401(http_client, base_url):
    req = HTTPRequest(base_url + "/personal/v4/accounts", headers=routing_headers)
    response = yield http_client.fetch(req)
    assert response.code == 401, "Expected 401 for a request without headers"


@pytest.mark.gen_test
def test_nordea_accounts(http_client, base_url):
    headers = {
        "Signature": "fake-signature",
        "X-IBM-Client-ID": "fake-client-id",
        "X-IBM-Client-Secret": "fake-client-secret",
        "X-Nordea-Originating-Date": "blah",
        "X-Nordea-Originating-Host": "blah2",
    }
    req = HTTPRequest(
        base_url + "/personal/v4/accounts", headers={**headers, **routing_headers,},
    )
    response = yield http_client.fetch(req)
    assert response.code == 200, "Expected 200 for a valid request"
    rb = json.loads(response.body)
    assert isinstance(rb, dict)
    assert_that(rb, has_key("group_header"))
    assert_that(rb, has_key("response"))
