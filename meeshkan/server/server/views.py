import json
import logging
import os
from urllib import parse
from urllib.parse import urlencode

from http_types import RequestBuilder, Request
# from ..utils.http_utils import split_path
from tornado.web import RequestHandler

logger = logging.getLogger(__name__)


class MockServerView(RequestHandler):
    SUPPORTED_METHODS = ["GET", "POST", "HEAD", "DELETE", "PATCH", "PUT", "OPTIONS"]

    def set_default_headers(self):
        self.set_header("Content-Type", 'application/json; charset="utf-8"')

    def get(self, **kwargs):
        self._serve()

    def post(self):
        self._serve()

    def head(self, **kwargs):
        self._serve()

    def delete(self, **kwargs):
        self._serve()

    def patch(self, **kwargs):
        self._serve()

    def put(self, **kwargs):
        self._serve()

    def options(self, **kwargs):
        self._serve()

    def _serve(self):
        query = parse.parse_qs(self.request.query)

        fullpath = "{}?{}".format(self.request.path, self.request.query) if query else self.request.path

        request = Request(Request(method=self.request.method.lower(),
                                  host=self.request.host,
                                  path=fullpath,
                                  pathname=self.request.path,
                                  protocol=self.request.protocol,
                                  query=query,
                                  body=self.request.body,
                                  bodyAsJson=self._extract_json_safely(self.request.body),
                                  headers={k:v for k,v in self.request.headers.get_all()}))
        RequestBuilder.validate(request)


        response = self.application.mocking_service.match(request)
        self.write(response['body'])

    def _extract_json_safely(self, text):
        if text:
            try:
                return json.loads(text)
            except Exception as e:
                pass

        return {}


