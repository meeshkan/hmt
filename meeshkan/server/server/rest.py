import logging
from typing import Mapping
from openapi_typed import OpenAPIObject
from http_types import Request, Response
import requests
import json
import copy

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
    
    def spew(self, request: Request, schemas: Mapping[str, OpenAPIObject]):
        _request = copy.deepcopy(request)
        _request['body'] = str(_request['body'])
        cur_schemas = schemas
        for endpoint in self._endpoints:
            res = requests.post(endpoint, data=json.dumps({'request': _request, 'schemas': cur_schemas }))
            cur_schemas = json.loads(res.text)
        return cur_schemas


rest_middleware_manager = RestMiddlewareManager()
