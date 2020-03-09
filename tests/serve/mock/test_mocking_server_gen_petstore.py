from tornado.httpclient import AsyncHTTPClient, HTTPRequest

import pytest
import json

from meeshkan.serve.mock.server import make_mocking_app
from meeshkan.serve.utils.routing import HeaderRouting


@pytest.fixture
def app():
    return make_mocking_app('tests/serve/mock/callbacks', 'tests/serve/mock/schemas/petstore', HeaderRouting())

URL = 'petstore.swagger.io'

@pytest.mark.gen_test
def test_mocking_server_pets(http_client, base_url):
    req = HTTPRequest(base_url+'/pets', headers={
        'Host': 'petstore.swagger.io'
    })
    response = yield http_client.fetch(req)
    assert response.code == 200
    rb = json.loads(response.body)
    assert type(rb) == type([])
    for pet in rb:
        assert type(pet['name']) == type("")

@pytest.mark.gen_test
def test_mocking_server_pet(http_client, base_url):
    req = HTTPRequest(base_url+'/pets/42', headers={
        'Host': 'petstore.swagger.io'
    })
    response = yield http_client.fetch(req)
    assert response.code == 200
    rb = json.loads(response.body)
    assert type(rb) == type({})
    assert type(rb['name']) == type("")
    assert type(rb['id']) == type(0)