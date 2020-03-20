import logging
from typing import Sequence

import requests
from http_types import Request
from http_types.utils import HttpExchangeWriter
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
        req = HttpExchangeWriter.to_dict(request)
        cs = {spec.source: convert_from_openapi(spec.api) for spec in specs}
        for endpoint in self._endpoints:
            res = requests.post(endpoint, json={"request": req, "schemas": cs})
            cs = res.json()
        return [
            OpenAPISpecification(convert_to_openapi(api), source)
            for source, api in cs.items()
        ]


rest_middleware_manager = RestMiddlewareManager()
