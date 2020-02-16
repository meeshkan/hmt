import json
import logging
import os
from urllib import parse
from urllib.parse import urlencode

from http_types import RequestBuilder, Request

from ..server.storage import storage_manager
from tornado.web import RequestHandler

logger = logging.getLogger(__name__)


class StorageView(RequestHandler):
    SUPPORTED_METHODS = ["DELETE"]

    def set_default_headers(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')

    def delete(self, **kwargs):
        storage_manager.clear()



