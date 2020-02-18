import json
from unittest.mock import Mock

import pytest
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
async def test_proxy(http_client, base_url, mocker):
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

    data_callback.log.assert_called_once()
