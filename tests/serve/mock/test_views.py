import json
from unittest.mock import Mock

import pytest
from http_types import HttpMethod, Protocol
from http_types.utils import ResponseBuilder
from tornado.httpclient import HTTPRequest

from meeshkan.serve.mock.callbacks import callback_manager
from meeshkan.serve.mock.log import Log
from meeshkan.serve.mock.response_matcher import ResponseMatcher
from meeshkan.serve.mock.scope import Scope
from meeshkan.serve.mock.server import make_mocking_app_
from meeshkan.serve.utils.routing import HeaderRouting

response = ResponseBuilder.from_dict(
    dict(
        statusCode=200,
        body='{"message": "hello"}',
        bodyAsJson=json.loads('{"message": "hello"}'),
        headers={},
    )
)
get_response_mock = Mock(return_value=response)


@pytest.fixture
def app():
    callback_manager.load("tests/serve/mock/callbacks")
    response_matcher = ResponseMatcher("tests/serve/mock/schemas/petstore")

    response_matcher.get_response = get_response_mock

    app = make_mocking_app_(
        callback_manager=callback_manager,
        response_matcher=response_matcher,
        router=HeaderRouting(),
        log=Log(Scope()),
    )
    return app


@pytest.mark.gen_test
def test_mocking_server_pets(http_client, base_url, app):

    req = HTTPRequest(base_url + "/pets", headers={"Host": "petstore.swagger.io"})
    http_response = yield http_client.fetch(req)
    assert 200 == http_response.code
    rb = json.loads(http_response.body)
    assert {"message": "hello"} == rb

    assert len(get_response_mock.call_args_list) == 1
    request = get_response_mock.call_args_list[0][0][0]
    assert HttpMethod.GET == request.method
    assert Protocol.HTTP == request.protocol
    assert "/pets" == request.pathname
    assert "/pets" == request.path
    assert {} == request.query
    assert "petstore.swagger.io" == request.host
    assert "petstore.swagger.io" == request.headers["Host"]
