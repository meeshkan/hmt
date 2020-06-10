import datetime
import logging
from dataclasses import asdict
from urllib import parse

from http_types import RequestBuilder
from tornado.web import RequestHandler

from ..utils.routing import Routing
from .log import Log
from .request_processor import RequestProcessor

logger = logging.getLogger(__name__)


class MockServerView(RequestHandler):
    _request_processor: RequestProcessor
    _router: Routing
    _log: Log

    SUPPORTED_METHODS = ["GET", "POST", "HEAD", "DELETE", "PATCH", "PUT", "OPTIONS"]

    def initialize(
        self, request_processor: RequestProcessor, router: Routing, http_log: Log,
    ):
        self._request_processor = request_processor
        self._router = router
        self._http_log = http_log

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
        route_info = self._router.route(self.request.path, headers)
        headers["Host"] = route_info.host

        query = parse.parse_qs(self.request.query)
        fullpath = (
            "{}?{}".format(route_info.path, self.request.query)
            if query
            else route_info.path
        )

        # ignoring type due to this error
        """
          46:34 - error: Argument of type 'str' cannot be assigned to parameter 'method' of type 'Literal['connect', 'head', 'trace', 'options', 'delete', 'patch', 'post', 'put', 'get']'
          'str' cannot be assigned to 'Literal['connect']'
          'str' cannot be assigned to 'Literal['head']'
          'str' cannot be assigned to 'Literal['trace']'
          'str' cannot be assigned to 'Literal['options']'
          'str' cannot be assigned to 'Literal['delete']'
        """
        request = RequestBuilder.from_dict(
            {
                "method": self.request.method.lower(),
                "host": route_info.host,
                "path": fullpath,
                "pathname": route_info.path,
                "protocol": route_info.scheme,
                "query": query,
                "body": self.request.body.decode("utf-8"),
                "headers": headers,
            }
        )

        logger.debug("Processing request: %s", asdict(request))
        response = self._request_processor.process(request)
        logger.debug("Resolved response: %s", asdict(response))

        for header, value in response.headers.items():
            self.set_header(header, value)
        self._http_log.put(request, response)
        self.set_status(response.statusCode)
        self.write(response.body)
        logger.debug("Handled writing response")
