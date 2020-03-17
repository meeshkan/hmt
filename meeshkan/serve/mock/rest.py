import json
import logging
from io import StringIO
from typing import Sequence

import requests
from http_types import HttpExchange, Request
from http_types.utils import HttpExchangeWriter, ResponseBuilder
from openapi_typed_2 import convert_from_openapi, convert_to_openapi

from meeshkan.serve.mock.specs import OpenAPISpecification

logger = logging.getLogger(__name__)


class RestMiddlewareManager:
    def __init__(self):
        self._endpoints = set([])

    def get(self):
        return list(self._endpoints)

    def clear(self, url=None):
        if not url:
            self._endpoints = set([])
        else:
            self._endpoints.remove(url)

    def add(self, url):
        self._endpoints.add(url)

    def spew(
        self, request: Request, specs: Sequence[OpenAPISpecification]
    ) -> Sequence[OpenAPISpecification]:
        req_io = StringIO()
        # TODO: this is hackish. is there a better way?
        HttpExchangeWriter(req_io).write(
            HttpExchange(
                request=request,
                response=ResponseBuilder.from_dict(
                    dict(statusCode=200, body="", headers={})
                ),
            )
        )
        # should only be one line... and why do we join with newline?
        req_io.seek(0)
        req = json.loads("\n".join([x for x in req_io]))["request"]
        cs = {spec.source: convert_from_openapi(spec.api) for spec in specs}
        for endpoint in self._endpoints:
            res = requests.post(
                endpoint, data=json.dumps({"request": req, "schemas": cs})
            )
            cs = json.loads(res.text)
        return [
            OpenAPISpecification(convert_to_openapi(api), source)
            for source, api in cs.items()
        ]


rest_middleware_manager = RestMiddlewareManager()
