from meeshkan.server import make_admin_app
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

import pytest
import json


@pytest.fixture
def app():
    return make_admin_app()

@pytest.mark.gen_test
def test_admin_server_middleware(http_client, base_url):
    req = HTTPRequest(base_url+'/admin/rest_middleware')
    response = yield http_client.fetch(req)
    assert response.code == 200
    assert json.loads(response.body) == []
    req = HTTPRequest(base_url+'/admin/rest_middleware/https://foo.bar.com/api/v2', method="POST", body='')
    response = yield http_client.fetch(req)
    assert response.code == 200
    req = HTTPRequest(base_url+'/admin/rest_middleware/https://foo.bar.com/api/v2', method="POST", body='')
    response = yield http_client.fetch(req)
    assert response.code == 200
    req = HTTPRequest(base_url+'/admin/rest_middleware/111', method="POST", body='')
    response = yield http_client.fetch(req)
    assert response.code == 200
    req = HTTPRequest(base_url+'/admin/rest_middleware')
    response = yield http_client.fetch(req)
    assert response.code == 200
    assert len(json.loads(response.body)) == 2
    assert 'https://foo.bar.com/api/v2' in json.loads(response.body)
    assert '111' in json.loads(response.body)