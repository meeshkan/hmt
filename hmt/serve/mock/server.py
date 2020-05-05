import logging
from typing import Optional

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application

from hmt.serve.mock.rest import RestMiddlewareManager
from hmt.serve.mock.storage.mock_data_store import MockDataStore

from ..admin.runner import start_admin
from ..mock.callbacks import callback_manager
from ..mock.request_processor import RequestProcessor
from ..mock.views import MockServerView
from ..utils.routing import PathRouting
from .log import FileSink, Log, NoSink
from .scope import Scope

logger = logging.getLogger(__name__)


class MockServer:
    def __init__(
        self,
        port,
        specs,
        scope: Optional[Scope] = None,
        callback_dir=None,
        admin_port=None,
        routing=PathRouting(),
        log_dir: Optional[str] = None,
    ):
        self._admin_port = admin_port
        self._port = port
        self._specs = specs
        self._routing = routing
        self._scope = scope or Scope()
        self._log = Log(self._scope, NoSink() if log_dir is None else FileSink(log_dir))

        self._mock_data_store = MockDataStore()
        self._rest_middleware_manager = RestMiddlewareManager(self._mock_data_store)
        self._callback_manager = callback_manager

        if callback_dir is not None:
            callback_manager.load(callback_dir)

        for spec in specs:
            self._mock_data_store.add_mock(spec)

        self._request_processor = RequestProcessor(
            self._specs,
            self._mock_data_store,
            self._callback_manager,
            self._rest_middleware_manager,
        )

    def run(self) -> None:
        if self._admin_port:
            start_admin(
                port=self._admin_port,
                scope=self._scope,
                mock_data_store=self._mock_data_store,
                rest_middleware_manager=self._rest_middleware_manager,
            )

        app = Application(
            [
                (
                    r"/.*",
                    MockServerView,
                    dict(
                        request_processor=self._request_processor,
                        router=self._routing,
                        http_log=self._log,
                    ),
                )
            ]
        )

        http_server = HTTPServer(app)
        http_server.listen(self._port)
        self.log_startup()
        IOLoop.current().start()

    def log_startup(self) -> None:
        for spec in self._specs:
            if not spec.api.servers:
                continue
            for path, path_item in spec.api.paths.items():
                for method in [
                    "get",
                    "put",
                    "post",
                    "delete",
                    "options",
                    "head",
                    "patch",
                    "trace",
                ]:
                    if getattr(path_item, method):
                        logger.info(
                            "- "
                            + method.upper().ljust(7)
                            + f" http://localhost:{self._port}/"
                            + spec.api.servers[0].url
                            + path
                        )

        logger.info("Meeshkan is running")
