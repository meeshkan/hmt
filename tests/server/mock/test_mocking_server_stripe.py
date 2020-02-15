from tools.meeshkan_server import make_mocking_app

import pytest
import json

@pytest.fixture
def app():
    return make_mocking_app('tests/server/mock/callbacks', 'gen', 'tests/server/mock/recordings', 'tests/server/mock/stripe_schema')


@pytest.mark.gen_test
#@pytest.mark.skip("takes too long due to a timeout, need to investigate")
def test_mocking_server_customers(http_client, base_url):
    response = yield http_client.fetch(base_url+'/v1/customers')
    assert response.code == 200
    rb = json.loads(response.body)
    assert type(rb) == type({})
