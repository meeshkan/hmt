import json
import logging
from io import StringIO
from typing import Sequence, Mapping, List

import requests
from http_types import HttpExchange, Request
from http_types.utils import HttpExchangeWriter, ResponseBuilder
from openapi_typed_2 import convert_from_openapi, convert_to_openapi

from meeshkan.serve.mock.specs import OpenAPISpecification

from meeshkan.serve.mock.data import storage_manager

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
        if len(self._endpoints) == 0:
            return specs

        req = HttpExchangeWriter.to_dict(request)
        cs = {spec.source: convert_from_openapi(spec.api) for spec in specs}
        for endpoint in self._endpoints:
            res = requests.post(endpoint, json={"request": req, "schemas": cs})
            cs = res.json()

        out: List[OpenAPISpecification] = []
        for name, dict_spec in cs.items():
            spec = convert_to_openapi(dict_spec)
            storage_manager.add_mock(name, spec)
            out.append(OpenAPISpecification(spec, name))
        return out


rest_middleware_manager = RestMiddlewareManager()
