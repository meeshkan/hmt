from tools.meeshkan_server import make_mocking_app

import pytest

@pytest.fixture
def app():
    return make_mocking_app('tests/server/mock/callbacks', 'gen', 'tests/server/mock/recordings', 'tests/server/mock/schemas')

@pytest.mark.gen_test
def test_mocking_server(http_client, base_url):
    response = yield http_client.fetch(base_url+'/pets')
    assert response.code == 200