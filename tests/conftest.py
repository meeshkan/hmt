import logging
from typing import Optional, Sequence

import pytest
from tornado.web import Application

from meeshkan.serve.mock.callbacks import callback_manager
from meeshkan.serve.mock.log import Log
from meeshkan.serve.mock.request_processor import RequestProcessor
from meeshkan.serve.mock.rest import RestMiddlewareManager
from meeshkan.serve.mock.specs import OpenAPISpecification
from meeshkan.serve.mock.storage.mock_data_store import MockDataStore
from meeshkan.serve.mock.views import MockServerView
from meeshkan.serve.utils.routing import Routing
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
                        log=log,
                    ),
                )
            ]
        )

    return _make_mocking_app


@pytest.fixture
def test_sink():
    return MockSink()


logging.root.setLevel(logging.DEBUG)
