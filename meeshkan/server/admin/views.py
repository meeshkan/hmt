import logging

from tornado.web import RequestHandler

from ..server.storage import storage_manager

logger = logging.getLogger(__name__)


class StorageView(RequestHandler):
    SUPPORTED_METHODS = ["DELETE"]

    def set_default_headers(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')

    def delete(self, **kwargs):
        storage_manager.clear()
