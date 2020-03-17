import json
import logging

from tornado.web import RequestHandler

from ..mock.rest import RestMiddlewareManager
from ..mock.scope import Scope
from ..mock.storage import StorageManager

logger = logging.getLogger(__name__)


class StorageView(RequestHandler):
    SUPPORTED_METHODS = ["DELETE"]

    def initialize(self, storage_manager: StorageManager):
        self.storage_manager = storage_manager

    def set_default_headers(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')

    def delete(self):
        self.storage_manager.clear()


class ScopeView(RequestHandler):
    SUPPORTED_METHODS = ["DELETE", "POST", "GET"]

    def initialize(self, scope: Scope):
        self.scope = scope

    def delete(self):
        self.scope.clear()

    def post(self):
        self.scope.set(self.get_body_argument("name"))

    def get(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')
        return self.write(
            dict() if self.scope.get() is None else dict(name=self.scope.get())
        )


class RestMiddlewaresView(RequestHandler):
    SUPPORTED_METHODS = ["DELETE", "GET"]

    def initialize(self, rest_middleware_manager: RestMiddlewareManager):
        self.rest_middleware_manager = rest_middleware_manager

    def set_default_headers(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')

    def delete(self):
        self.rest_middleware_manager.clear()

    def get(self):
        self.write(json.dumps(self.rest_middleware_manager.get()))


class RestMiddlewareView(RequestHandler):
    SUPPORTED_METHODS = ["DELETE", "POST"]

    def initialize(self, rest_middleware_manager: RestMiddlewareManager):
        self.rest_middleware_manager = rest_middleware_manager

    def set_default_headers(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')

    def delete(self, url):
        self.rest_middleware_manager.clear(url)

    def post(self, url):
        self.rest_middleware_manager.add(url)
