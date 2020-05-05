import json

import pytest
from tornado.httpclient import HTTPRequest

from hmt.serve.mock.log import Log
from hmt.serve.mock.scope import Scope
from hmt.serve.mock.specs import load_specs
from hmt.serve.utils.routing import HeaderRouting


@pytest.fixture
def app(mocking_app, test_sink):
    return mocking_app(
        "tests/serve/mock/callbacks",
        load_specs("tests/serve/mock/schemas/petstore"),
        HeaderRouting(),
        Log(Scope(), test_sink),
    )


URL = "petstore.swagger.io"


@pytest.mark.gen_test
def test_mocking_server_pets(http_client, base_url, test_sink):
    req = HTTPRequest(base_url + "/pets", headers={"Host": "petstore.swagger.io"})
    response = yield http_client.fetch(req)
    assert response.code == 200
    rb = json.loads(response.body)
    assert isinstance(rb, list)
    for pet in rb:
        assert isinstance(pet["name"], str)
    assert len(test_sink.interactions) == 1
    assert test_sink.interactions[0]["request"]["path"] == "/pets"


@pytest.mark.gen_test
def test_mocking_server_pet(http_client, base_url):
    req = HTTPRequest(base_url + "/pets/42", headers={"Host": "petstore.swagger.io"})
    response = yield http_client.fetch(req)
    assert response.code == 200
    rb = json.loads(response.body)
    assert isinstance(rb, dict)
    assert isinstance(rb["name"], str)
    assert isinstance(rb["id"], int)
