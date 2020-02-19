import json
from unittest.mock import Mock

import requests_mock
import pytest
from http_types import Response
from tornado.httpclient import HTTPRequest

from meeshkan.server.server.rest import rest_middleware_manager
from meeshkan.server import make_mocking_app
from meeshkan.server.utils.routing import HeaderRouting


@pytest.fixture
def app():
    return make_mocking_app('tests/server/mock/callbacks', 'tests/server/mock/petstore_schema',
                            HeaderRouting())

@pytest.fixture(autouse=True)
def setup():
    rest_middleware_manager.add("https://api.hello.world")
    yield True
    rest_middleware_manager.clear("https://api.hello.world")

@pytest.mark.gen_test
def test_rest_middleware(http_client, base_url, app):
    
    req = HTTPRequest(base_url + '/pets', headers={
        'Host': 'petstore.swagger.io'
    })
    with requests_mock.Mocker() as m:
        m.post("https://api.hello.world", json={
            'petstore': {
                'servers': [{'url': 'http://petstore.swagger.io'}],
                'paths': {
                    '/pets': {
                        'get': {
                            'responses': {
                                '200': {
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                'type': 'number',
                                                'enum': [42]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        })
        response = yield http_client.fetch(req)
        assert 42 == json.loads(response.body)

