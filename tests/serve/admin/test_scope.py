import json

import pytest
from tornado.httpclient import HTTPRequest

from meeshkan.serve.admin import make_admin_app
from meeshkan.serve.mock.scope import Scope

scope = Scope()


@pytest.fixture
def app():
    return make_admin_app(scope=scope)


@pytest.fixture(autouse=True)
def setup():
    yield True
    scope.clear()


@pytest.mark.gen_test
def test_admin_server_scope(http_client, base_url):
    body = "name=foo"
    req = HTTPRequest(
        base_url + "/admin/scope",
        method="POST",
        body=body,
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "content-length": len(body),
        },
    )
    response = yield http_client.fetch(req)
    assert response.code == 200
    req = HTTPRequest(base_url + "/admin/scope")
    response = yield http_client.fetch(req)
    assert response.code == 200
    assert json.loads(response.body)["name"] == "foo"
    req = HTTPRequest(base_url + "/admin/scope", method="DELETE")
    yield http_client.fetch(req)
    req = HTTPRequest(base_url + "/admin/scope")
    response = yield http_client.fetch(req)
    assert response.code == 200
    assert not ("name" in json.loads(response.body))
