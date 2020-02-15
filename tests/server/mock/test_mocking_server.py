from tools.meeshkan_server import make_mocking_app

import pytest
import json

@pytest.fixture
def app():
    return make_mocking_app('tests/server/mock/callbacks', 'gen', 'tests/server/mock/recordings', 'tests/server/mock/schemas')

@pytest.mark.gen_test
def test_mocking_server_pets(http_client, base_url):
    response = yield http_client.fetch(base_url+'/pets')
    assert response.code == 200
    rb = json.loads(response.body)
    assert type(rb) == type([])
    for pet in rb:
        assert type(pet['name']) == type("")

@pytest.mark.gen_test
def test_mocking_server_pet(http_client, base_url):
    response = yield http_client.fetch(base_url+'/pets/42')
    assert response.code == 200
    rb = json.loads(response.body)
    assert type(rb) == type({})
    assert type(rb['name']) == type("")
    assert type(rb['id']) == type(0)