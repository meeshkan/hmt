import logging
from typing import Sequence

import requests
from http_types import Request
from http_types.utils import HttpExchangeWriter
from openapi_typed_2 import convert_from_openapi, convert_to_openapi

from hmt.serve.mock.refs import make_definitions_from_spec
from hmt.serve.mock.specs import OpenAPISpecification

logger = logging.getLogger(__name__)


class RestMiddlewareManager:
    def __init__(self, mock_data_store):
        self._mock_data_store = mock_data_store
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

        out = []
        for name, dict_spec in cs.items():
            spec = convert_to_openapi(dict_spec)
            out.append(
                OpenAPISpecification(
                    spec, name, definitions=make_definitions_from_spec(spec)
                )
            )

        for spec in out:
            self._mock_data_store.add_mock(spec)

        return out
