import json
import urllib.parse
from unittest.mock import Mock

import pytest
from http_types import HttpMethod, Protocol
from tornado.httpclient import HTTPRequest
from tornado.testing import bind_unused_port

from meeshkan.serve.mock.log import Log
from meeshkan.serve.mock.scope import Scope
from meeshkan.serve.mock.server import make_mocking_app
from meeshkan.serve.mock.specs import load_specs
from meeshkan.serve.record.proxy import RecordProxy
from meeshkan.serve.utils.data_callback import DataCallback
from meeshkan.serve.utils.routing import HeaderRouting, PathRouting, StaticRouting


@pytest.fixture
def app():
    return make_mocking_app(
        "tests/serve/mock/callbacks",
        load_specs("tests/serve/mock/schemas/petstore"),
        StaticRouting("http://petstore.swagger.io"),
        log=Log(Scope()),
    )


@pytest.mark.gen_test
def test_path_proxy(http_client, base_url):
    server = None
    data_callback = Mock(spec=DataCallback)
    try:
        sock, port = bind_unused_port()
        server = RecordProxy(data_callback, PathRouting())
        server.add_socket(sock)
        response = yield http_client.fetch(
            "http://localhost:{}/{}/pets".format(port, base_url)
        )

        assert 200 == response.code
        rb = json.loads(response.body)
        assert type([]) == type(rb)
    finally:
        if server is not None:
            server.stop()

    yield http_client.close()

    assert len(data_callback.log.call_args_list) == 1

    base_url_sp = urllib.parse.urlsplit(base_url)
    host = "{}:{}".format(base_url_sp.hostname, base_url_sp.port)

    request = data_callback.log.call_args_list[0][0][0]
    assert HttpMethod("get") == request.method
    assert Protocol("http") == request.protocol
    assert "/pets" == request.pathname
    assert "/pets" == request.path
    assert {} == request.query
    assert host == request.host
    assert host == request.headers["Host"]

    response = data_callback.log.call_args_list[0][0][1]
    assert 200 == response.statusCode
    assert isinstance(response.bodyAsJson, list)
    assert isinstance(response.body, str)
    assert len(response.body) > 0


@pytest.mark.gen_test
def test_header_proxy(http_client, base_url):
    server = None
    data_callback = Mock(spec=DataCallback)
    try:
        sock, port = bind_unused_port()
        server = RecordProxy(data_callback, HeaderRouting())
        server.add_socket(sock)
        host_url = urllib.parse.urlsplit(base_url)
        response = yield http_client.fetch(
            HTTPRequest(
                "http://localhost:{}/pets".format(port),
                headers={
                    "host": "{}:{}".format(host_url.hostname, host_url.port),
                    "X-Meeshkan-Scheme": "http",
                },
            )
        )

        assert 200 == response.code
        rb = json.loads(response.body)
        assert type([]) == type(rb)
    finally:
        if server is not None:
            server.stop()

    yield http_client.close()

    assert len(data_callback.log.call_args_list) == 1

    base_url_sp = urllib.parse.urlsplit(base_url)
    host = "{}:{}".format(base_url_sp.hostname, base_url_sp.port)

    request = data_callback.log.call_args_list[0][0][0]
    assert HttpMethod("get") == request.method
    assert Protocol("http") == request.protocol
    assert "/pets" == request.pathname
    assert "/pets" == request.path
    assert {} == request.query
    assert host == request.host
    assert host == request.headers["Host"]

    response = data_callback.log.call_args_list[0][0][1]
    assert 200 == response.statusCode
    assert isinstance(response.bodyAsJson, list)
    assert isinstance(response.body, str)
    assert len(response.body) > 0
