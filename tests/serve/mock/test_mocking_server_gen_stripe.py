import json

import pytest

from hmt.serve.mock.log import Log
from hmt.serve.mock.scope import Scope
from hmt.serve.mock.specs import load_specs
from hmt.serve.utils.routing import PathRouting


@pytest.fixture
def app(mocking_app):
    return mocking_app(
        "tests/serve/mock/callbacks",
        load_specs("tests/serve/mock/schemas/stripe"),
        PathRouting(),
        Log(Scope()),
    )


@pytest.mark.gen_test(timeout=10)
# @pytest.mark.skip("takes too long due to a timeout, need to investigate")
def test_mocking_server_customers(http_client, base_url):
    response = yield http_client.fetch(
        base_url + "/https://api.stripe.com/v1/customers"
    )
    assert response.code == 200
    rb = json.loads(response.body)
    assert isinstance(rb, dict)
