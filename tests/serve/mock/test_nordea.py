import json
import logging

import pytest
from hamcrest import assert_that, has_key, is_
from tornado.httpclient import HTTPClientError, HTTPRequest

from hmt.serve.mock.log import Log
from hmt.serve.mock.scope import Scope
from hmt.serve.mock.specs import load_specs
from hmt.serve.utils.routing import PathRouting

logger = logging.getLogger(__name__)
logging.basicConfig(level="DEBUG")

routing = PathRouting()
log = Log(Scope())
specs = load_specs("tests/serve/mock/schemas/nordea")


@pytest.fixture
def app(mocking_app):
    return mocking_app(None, specs, PathRouting(), log,)


def make_sandbox_url(base_url, path: str):
    return f"{base_url}/https://api.nordeaopenbanking.com{path}"


class TestNordea:
    @pytest.mark.gen_test
    async def test_nordea_authorize_returns_302(self, http_client, base_url):
        redirect_uri = "http://httpbin.org/get"
        query = f"state=fake&client_id=CLIENT_ID&scope=ACCOUNTS_BASIC,ACCOUNTS_BALANCES,ACCOUNTS_DETAILS,ACCOUNTS_TRANSACTIONS,PAYMENTS_MULTIPLE,CARDS_INFORMATION,CARDS_TRANSACTIONS&duration=129600&redirect_uri={redirect_uri}&country=FI"
        url = make_sandbox_url(base_url, path=f"/personal/v4/authorize?{query}")
        req = HTTPRequest(url, follow_redirects=False)
        with pytest.raises(HTTPClientError) as e:  # type: ignore
            await http_client.fetch(req)
        assert_that(e.value.code, is_(302))

    @pytest.mark.skip("Returning 401 for invalid auth not implemented")
    @pytest.mark.gen_test
    async def test_nordea_accounts_returns_401(self, http_client, base_url):
        url = make_sandbox_url(base_url, path="/personal/v4/accounts")
        req = HTTPRequest(url)
        try:
            await http_client.fetch(req)
            pytest.fail("Expected failure without auth")
        except HTTPClientError as e:
            assert e.code == 401, "Expected 401 without auth"

    @pytest.mark.skip("Returns randomly different status codes for a valid request")
    @pytest.mark.gen_test
    async def test_nordea_accounts(self, http_client, base_url):
        headers = {
            "Signature": "fake-signature",
            "X-IBM-Client-ID": "fake-client-id",
            "X-IBM-Client-Secret": "fake-client-secret",
            "X-Nordea-Originating-Date": "blah",
            "X-Nordea-Originating-Host": "blah2",
        }
        url = make_sandbox_url(base_url, path="/personal/v4/accounts")
        req = HTTPRequest(url, headers=headers)
        response = await http_client.fetch(req)
        assert response.code == 200, "Expected 200 for a valid request"
        rb = json.loads(response.body)
        assert isinstance(rb, dict)
        assert_that(rb, has_key("group_header"))
        assert_that(rb, has_key("response"))
