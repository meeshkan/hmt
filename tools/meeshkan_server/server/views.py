import json
import logging
import os
from urllib import parse
from urllib.parse import urlencode

from http_types import RequestBuilder, Request
from tools.meeshkan_server.utils.http_utils import split_path
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
        # print(self.request.arguments)
        # print(self.request.path)
        # print(self.request.headers)
        # print(self.request.body)
        # print()

        splits = split_path(self.request.path)
        scheme, host = splits[0], splits[1]
        path = os.path.join('/', *splits[2:])
        query = parse.parse_qs(self.request.query)

        fullpath = "{}?{}".format(path, self.request.query) if query else path

        request = Request(Request(method=self.request.method.lower(),
                                  host=host,
                                  path=fullpath,
                                  pathname=path,
                                  protocol=scheme,
                                  query=query,
                                  body=self.request.body,
                                  bodyAsJson=self._extract_json_safely(self.request.body),
                                  headers=self.request.headers))
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


