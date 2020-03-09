import logging
from typing import Mapping
from openapi_typed_2 import OpenAPIObject, convert_to_openapi, convert_from_openapi
from http_types import Request
from http_types.utils import HttpExchangeWriter, ResponseBuilder, HttpExchange
from io import StringIO
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
    
    def spew(self, request: Request, schemas: Mapping[str, OpenAPIObject]) -> Mapping[str, OpenAPIObject]:
        cur_schemas = schemas
        req_io = StringIO()
        # TODO: this is hackish. is there a better way?
        HttpExchangeWriter(req_io).write(HttpExchange(request=request, response=ResponseBuilder.from_dict(dict(statusCode=200,body='',headers={}))))
        # should only be one line... and why do we join with newline?
        req_io.seek(0)
        req = json.loads('\n'.join([x for x in req_io]))['request']
        cs = {k: convert_from_openapi(v) for k, v in cur_schemas.items()}
        for endpoint in self._endpoints:
            res = requests.post(endpoint, data=json.dumps({'request': req, 'schemas': cs }))
            cs = json.loads(res.text)
        out: Mapping[str, OpenAPIObject] = {str(k): convert_to_openapi(v) for k, v in cs.items()}
        return out


rest_middleware_manager = RestMiddlewareManager()
