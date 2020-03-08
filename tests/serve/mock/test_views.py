import json
from unittest.mock import Mock

import pytest
from http_types import HttpMethod, Protocol
from http_types.utils import ResponseBuilder
from tornado.httpclient import HTTPRequest

from meeshkan.serve.mock.server import make_mocking_app
from meeshkan.serve.utils.routing import HeaderRouting

@pytest.fixture
def app():
    return make_mocking_app('tests/serve/mock/callbacks', 'tests/serve/mock/schemas/petstore',
                            HeaderRouting())


@pytest.mark.gen_test
def test_mocking_server_pets(http_client, base_url, app):
    response = ResponseBuilder.from_dict(
        dict(statusCode=200, body='{"message": "hello"}', bodyAsJson=json.loads('{"message": "hello"}'),
             headers={}))
    app.response_matcher.get_response = Mock(return_value=response)

    req = HTTPRequest(base_url + '/pets', headers={
        'Host': 'petstore.swagger.io'
    })
    http_response = yield http_client.fetch(req)
    assert 200 == http_response.code
    rb = json.loads(http_response.body)
    assert {'message': "hello"} == rb

    assert len(app.response_matcher.get_response.call_args_list) == 1
    request = app.response_matcher.get_response.call_args_list[0][0][0]
    assert HttpMethod.GET == request.method
    assert Protocol.HTTP == request.protocol
    assert '/pets' == request.pathname
    assert '/pets' == request.path
    assert {} == request.query
    assert 'petstore.swagger.io' == request.host
    assert 'petstore.swagger.io' == request.headers['Host']
