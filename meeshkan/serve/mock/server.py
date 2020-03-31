import logging
from typing import Optional, Sequence

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application

from meeshkan.serve.mock.rest import RestMiddlewareManager
from meeshkan.serve.mock.storage.manager import StorageManager

from ..admin.runner import start_admin
from ..mock.callbacks import CallbackManager, callback_manager
from ..mock.request_processor import RequestProcessor
from ..mock.specs import OpenAPISpecification
from ..mock.views import MockServerView
from ..utils.routing import PathRouting, Routing
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

        self._storage_manager = StorageManager()
        self._rest_middleware_manager = RestMiddlewareManager(self._storage_manager)
        self._callback_manager = callback_manager

        if callback_dir is not None:
            callback_manager.load(callback_dir)

        self._request_processor = RequestProcessor(
            self._specs,
            self._storage_manager,
            self._callback_manager,
            self._rest_middleware_manager,
        )

    def run(self) -> None:
        if self._admin_port:
            start_admin(
                port=self._admin_port,
                scope=self._scope,
                storage_manager=self._storage_manager,
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
                        log=self._log,
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
