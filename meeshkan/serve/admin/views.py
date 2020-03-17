import logging

from tornado.web import RequestHandler

from ..mock.storage import storage_manager
from ..mock.rest import rest_middleware_manager
from ..mock.scope import scope_manager
import json

logger = logging.getLogger(__name__)


class StorageView(RequestHandler):
    SUPPORTED_METHODS = ["DELETE"]

    def set_default_headers(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')

    def delete(self):
        storage_manager.clear()

class ScopeView(RequestHandler):
    SUPPORTED_METHODS = ["DELETE", "POST", "GET"]
    
    def delete(self):
        scope_manager.clear()

    def post(self):
        scope_manager.set(self.get_body_argument("name"))
    
    def get(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')
        return self.write(dict() if scope_manager.get() is None else dict(name=scope_manager.get()))


class RestMiddlewaresView(RequestHandler):
    SUPPORTED_METHODS = ["DELETE", "GET"]

    def set_default_headers(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')

    def delete(self):
        rest_middleware_manager.clear()

    def get(self):
        self.write(json.dumps(rest_middleware_manager.get()))


class RestMiddlewareView(RequestHandler):
    SUPPORTED_METHODS = ["DELETE", "POST"]

    def set_default_headers(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')

    def delete(self, url):
        rest_middleware_manager.clear(url)

    def post(self, url):
        rest_middleware_manager.add(url)
