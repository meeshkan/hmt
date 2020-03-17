import json

import pytest
from tornado.httpclient import HTTPRequest

from meeshkan.serve.mock.server import make_mocking_app
from meeshkan.serve.mock.specs import load_specs
from meeshkan.serve.utils.routing import HeaderRouting


@pytest.fixture
def app():
    return make_mocking_app(
        "tests/serve/mock/callbacks",
        load_specs("tests/serve/mock/schemas/petstore"),
        HeaderRouting(),
    )


URL = "petstore.swagger.io"


@pytest.mark.gen_test
def test_mocking_server_pets(http_client, base_url):
    req = HTTPRequest(base_url + "/pets", headers={"Host": "petstore.swagger.io"})
    response = yield http_client.fetch(req)
    assert response.code == 200
    rb = json.loads(response.body)
    assert isinstance(rb, list)
    for pet in rb:
        assert isinstance(pet["name"], str)


@pytest.mark.gen_test
def test_mocking_server_pet(http_client, base_url):
    req = HTTPRequest(base_url + "/pets/42", headers={"Host": "petstore.swagger.io"})
    response = yield http_client.fetch(req)
    assert response.code == 200
    rb = json.loads(response.body)
    assert isinstance(rb, dict)
    assert isinstance(rb["name"], str)
    assert isinstance(rb["id"], int)
