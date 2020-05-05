import logging

from tornado.httpserver import HTTPServer
from tornado.web import Application

from hmt.serve.admin.views import (
    RestMiddlewaresView,
    RestMiddlewareView,
    ScopeView,
    StorageView,
)
from hmt.serve.mock.rest import RestMiddlewareManager
from hmt.serve.mock.storage.mock_data_store import MockDataStore

from ..mock.scope import Scope

logger = logging.getLogger(__name__)


def make_admin_app(
    scope: Scope,
    mock_data_store: MockDataStore,
    rest_middleware_manager: RestMiddlewareManager,
):
    storage_view_deps = dict(mock_data_store=mock_data_store)
    rest_middleware_deps = dict(rest_middleware_manager=rest_middleware_manager)
    scope_view_deps = dict(scope=scope)
    return Application(
        [
            (r"/admin/scope", ScopeView, scope_view_deps),
            (r"/admin/storage(?:/(.*))?", StorageView, storage_view_deps),
            (
                r"/admin/middleware/rest/pregen",
                RestMiddlewaresView,
                rest_middleware_deps,
            ),
            (
                r"/admin/middleware/rest/pregen/(.+)",
                RestMiddlewareView,
                rest_middleware_deps,
            ),
        ]
    )


def start_admin(
    port: int,
    scope: Scope,
    mock_data_store: MockDataStore,
    rest_middleware_manager: RestMiddlewareManager,
):
    app = make_admin_app(scope, mock_data_store, rest_middleware_manager)
    http_server = HTTPServer(app)
    http_server.listen(port)
    logger.info("- Admin   http://localhost:%s/admin", port)
