import json
import logging
import os

from typing import cast
import yaml
from http_types import Request, Response, HttpExchange, RequestBuilder, ResponseBuilder

from ...schemabuilder.builder import BASE_SCHEMA, update_openapi

logger = logging.getLogger(__name__)


class DataCallback:
    def log(self, request: Request, response: Response):
        raise NotImplementedError()


class RequestLoggingCallback():
    _log_dir: str
    _schema_dir: str
    def __init__(self, recording=False, log_dir=None, schema_dir=None, append=True):
        self._recording = recording
        self._append = append
        self._log_dir = log_dir
        self._schema_dir = schema_dir

        self._logs = {}
        self._schemas = {}

        if self._recording:
            if not os.path.exists(self._log_dir):
                os.makedirs(self._log_dir)
            if not os.path.exists(self._schema_dir):
                os.makedirs(self._schema_dir)

    def log(self, request: Request, response: Response):
        RequestBuilder.validate(request)
        ResponseBuilder.validate(response)

        host = request['headers']['Host']
        reqres = HttpExchange(request=request, response=response)
        if not host in self._logs:
            log_file = os.path.join(self._log_dir, '{}.jsonl'.format(host))
            if self._append and os.path.exists(log_file):
                self._logs[host] = open(log_file, 'a')
            else:
                self._logs[host] = open(log_file, 'w')

        self._logs[host].write(json.dumps(reqres))
        self._logs[host].write('\n')

        schema_dir = os.path.join(self._schema_dir, cast(str, host))
        if not os.path.exists(schema_dir):
            os.makedirs(schema_dir)

        schema_file = os.path.join(schema_dir, 'openapi.yaml')

        if not host in self._schemas:
            if os.path.exists(schema_file) and self._append:
                with open(schema_file, 'r') as f:
                    self._schemas[host] = yaml.load(f)
            else:
                self._schemas[host] = BASE_SCHEMA

        self._schemas[host] = update_openapi(self._schemas[host], reqres)

        with open(schema_file, 'w') as f:
            yaml.dump(self._schemas[host], f)

        logger.debug('Updated logs and scheme for host %s', host)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for f in self._logs.values():
            f.close()
