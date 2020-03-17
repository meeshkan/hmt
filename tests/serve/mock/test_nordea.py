import json

import pytest
from tornado.httpclient import HTTPRequest
from hamcrest import assert_that, has_key

from meeshkan.serve.mock.server import make_mocking_app
from meeshkan.serve.utils.routing import HeaderRouting


@pytest.fixture
def app():
    return make_mocking_app(
        "tests/serve/mock/callbacks", "tests/serve/mock/schemas/nordea", HeaderRouting()
    )


@pytest.mark.gen_test
def test_nordea_accounts(http_client, base_url):
    req = HTTPRequest(
        base_url + "/personal/v4/accounts",
        headers={"Host": "api.nordeaopenbanking.com", "X-Meeshkan-Scheme": "https"},
    )
    response = yield http_client.fetch(req)
    assert response.code == 200
    rb = json.loads(response.body)
    assert isinstance(rb, dict)
    assert_that(rb, has_key("group_header"))
    assert_that(rb, has_key("response"))
