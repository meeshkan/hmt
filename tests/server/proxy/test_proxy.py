import json
import urllib.parse
from unittest.mock import Mock

import pytest
from http_types import Request, Response
from tornado.testing import bind_unused_port

from meeshkan.server import make_mocking_app
from meeshkan.server.proxy.proxy import RecordProxy
from meeshkan.server.utils.data_callback import DataCallback
from meeshkan.server.utils.routing import PathRouting, StaticRouting


@pytest.fixture
def app():
    return make_mocking_app('tests/server/mock/callbacks', 'tests/server/mock/petstore_schema',
                            StaticRouting('http://petstore.swagger.io'))


@pytest.mark.gen_test
def test_proxy(http_client, base_url):
    server = None
    data_callback = Mock(spec=DataCallback)
    try:
        sock, port = bind_unused_port()
        server = RecordProxy(data_callback, PathRouting())
        server.add_socket(sock)
        response = yield http_client.fetch('http://localhost:{}/{}/pets'.format(port, base_url))

        assert response.code == 200
        rb = json.loads(response.body)
        assert type(rb) == type([])
    finally:
        if server is not None:
            server.stop()

    yield http_client.close()

    class RequestMatcher:
        def __eq__(self, other: Request):
            return other['method'] == 'get' and \
                   other['pathname'] == '/pets' and \
                   other['path'] == '/pets' and \
                   other['query'] == {}

    class ResponseMatcher:
        def __eq__(self, other: Response):
            return

    # data_callback.log.assert_called_with(RequestMatcher(), ResponseMatcher())

    assert len(data_callback.log.call_args_list) == 1

    base_url_sp = urllib.parse.urlsplit(base_url)
    host = '{}:{}'.format(base_url_sp.hostname, base_url_sp.port)

    request = data_callback.log.call_args_list[0][0][0]
    assert 'get' == request['method']
    assert 'http' == request['protocol']
    assert '/pets' == request['pathname']
    assert '/pets' == request['path']
    assert {} == request['query']
    assert host == request['host']
    assert host == request['headers']['Host']

    response = data_callback.log.call_args_list[0][0][1]
    assert 200 == response['statusCode']
    assert isinstance(response['bodyAsJson'], list)
    assert isinstance(response['body'], str)
    assert len(response['body']) > 0
