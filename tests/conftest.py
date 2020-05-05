import logging
from typing import Optional, Sequence

import pytest
from tornado.web import Application

from hmt.serve.mock.callbacks import callback_manager
from hmt.serve.mock.log import Log
from hmt.serve.mock.request_processor import RequestProcessor
from hmt.serve.mock.rest import RestMiddlewareManager
from hmt.serve.mock.specs import OpenAPISpecification
from hmt.serve.mock.storage.mock_data_store import MockDataStore
from hmt.serve.mock.views import MockServerView
from hmt.serve.utils.routing import Routing
from tests.util import MockSink


@pytest.fixture()
def mock_data_store():
    return MockDataStore()


@pytest.fixture()
def rest_middleware_manager(mock_data_store):
    return RestMiddlewareManager(mock_data_store)


@pytest.fixture()
def request_processor(mock_data_store, rest_middleware_manager):
    def _rp(specs):
        for spec in specs:
            mock_data_store.add_mock(spec)

        return RequestProcessor(
            specs, mock_data_store, callback_manager, rest_middleware_manager
        )

    return _rp


@pytest.fixture()
def mocking_app(request_processor):
    def _make_mocking_app(
        callback_dir: Optional[str],
        specs: Sequence[OpenAPISpecification],
        routing: Routing,
        log: Log,
    ):
        if callback_dir is not None:
            callback_manager.load(callback_dir)

        return Application(
            [
                (
                    r"/.*",
                    MockServerView,
                    dict(
                        request_processor=request_processor(specs),
                        router=routing,
                        http_log=log,
                    ),
                )
            ]
        )

    return _make_mocking_app


@pytest.fixture
def test_sink():
    return MockSink()


logging.root.setLevel(logging.DEBUG)
