import json
import logging
from typing import cast
from urllib import parse

from http_types import RequestBuilder
from tornado.web import RequestHandler

from meeshkan.server.server.callbacks import callback_manager

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
        headers = {k: v for k, v in self.request.headers.get_all()}
        route_info = self.application.router.route(self.request.path, headers)
        headers['Host'] = route_info.host

        query = parse.parse_qs(self.request.query)
        fullpath = "{}?{}".format(route_info.path, self.request.query) if query else route_info.path

        # ignoring type due to this error
        '''
          46:34 - error: Argument of type 'str' cannot be assigned to parameter 'method' of type 'Literal['connect', 'head', 'trace', 'options', 'delete', 'patch', 'post', 'put', 'get']'
          'str' cannot be assigned to 'Literal['connect']'
          'str' cannot be assigned to 'Literal['head']'
          'str' cannot be assigned to 'Literal['trace']'
          'str' cannot be assigned to 'Literal['options']'
          'str' cannot be assigned to 'Literal['delete']'
        '''
        request = RequestBuilder.from_dict({
                            'method': self.request.method.lower(),
                            'host': route_info.host,
                            'path': fullpath,
                            'pathname': route_info.path,
                            'protocol': route_info.scheme,
                            'query': query,
                            'body': str(self.request.body),
                            'bodyAsJson': self._extract_json_safely(self.request.body),
                            'headers': headers})

        logger.debug(request)
        response = callback_manager(request, self.application.response_matcher.get_response(request))
        for header, value in response.headers.items():
            self.set_header(header, value)

        self.write(response.body)

    def _extract_json_safely(self, text):
        if text:
            try:
                return json.loads(text)
            except Exception as e:
                pass

        return {}
