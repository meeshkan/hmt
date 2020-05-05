import json
from unittest.mock import Mock

import pytest
from http_types import HttpMethod, Protocol
from http_types.utils import ResponseBuilder
from tornado.httpclient import HTTPRequest

from hmt.serve.mock.log import Log
from hmt.serve.mock.scope import Scope
from hmt.serve.mock.specs import load_specs
from hmt.serve.utils.routing import HeaderRouting

response = ResponseBuilder.from_dict(
    dict(
        statusCode=200,
        body='{"message": "hello"}',
        bodyAsJson=json.loads('{"message": "hello"}'),
        headers={},
    )
)
process_mock = Mock(return_value=response)


@pytest.fixture()
def request_processor(request_processor):
    def _rp(specs):
        rp = request_processor(specs)
        rp.process = process_mock
        return rp

    return _rp


@pytest.fixture
def app(mocking_app):
    return mocking_app(
        "tests/serve/mock/callbacks",
        load_specs("tests/serve/mock/schemas/petstore"),
        HeaderRouting(),
        Log(Scope()),
    )


@pytest.mark.gen_test
def test_mocking_server_pets(http_client, base_url, app):

    req = HTTPRequest(base_url + "/pets", headers={"Host": "petstore.swagger.io"})
    http_response = yield http_client.fetch(req)
    assert 200 == http_response.code
    rb = json.loads(http_response.body)
    assert {"message": "hello"} == rb

    assert len(process_mock.call_args_list) == 1
    request = process_mock.call_args_list[0][0][0]
    assert HttpMethod.GET == request.method
    assert Protocol.HTTP == request.protocol
    assert "/pets" == request.pathname
    assert "/pets" == request.path
    assert {} == request.query
    assert "petstore.swagger.io" == request.host
    assert "petstore.swagger.io" == request.headers["Host"]
