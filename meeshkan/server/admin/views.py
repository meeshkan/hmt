import json
import logging
import os
from urllib import parse
from urllib.parse import urlencode

from http_types import RequestBuilder, Request

from ..server.storage import storage_manager
from ..server.rest import rest_middleware_manager
from tornado.web import RequestHandler

logger = logging.getLogger(__name__)


class StorageView(RequestHandler):
    SUPPORTED_METHODS = ["DELETE"]

    def set_default_headers(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')

    def delete(self):
        storage_manager.clear()


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
        



