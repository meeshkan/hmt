import json
import logging
import os
from typing import cast

import yaml
from http_types import Request, Response, HttpExchange, HttpExchangeWriter, RequestBuilder, ResponseBuilder

from meeshkan.schemabuilder.update_mode import UpdateMode
from ...schemabuilder.builder import BASE_SCHEMA, update_openapi

logger = logging.getLogger(__name__)


class DataCallback:
    def log(self, request: Request, response: Response):
        raise NotImplementedError()


class RequestLoggingCallback():
    _log_dir: str
    _specs_dir: str

    def __init__(self, log_dir, specs_dir, update_mode, append=True):
        self._log_dir = log_dir
        self._specs_dir = specs_dir
        self._update_mode = update_mode
        self._append = append

        self._logs = {}
        self._specs = {}

        if not os.path.exists(self._log_dir):
            os.makedirs(self._log_dir)
        if not os.path.exists(self._specs_dir):
            os.makedirs(self._specs_dir)

    def log(self, request: Request, response: Response):
        RequestBuilder.validate(request)
        ResponseBuilder.validate(response)

        host = request.host
        reqres = HttpExchange(request=request, response=response)
        if not host in self._logs:
            log_file = os.path.join(self._log_dir, '{}.jsonl'.format(host))
            if self._append and os.path.exists(log_file):
                self._logs[host] = open(log_file, 'a')
            else:
                self._logs[host] = open(log_file, 'w')

        HttpExchangeWriter(self._logs[host]).write(reqres)
        self._logs[host].write('\n')
        self._logs[host].flush()

        logger.debug('Updated logs for host %s', host)

        if self._update_mode:
            spec_file = os.path.join(self._specs_dir, '{}_{}.yaml'.format(host, self._update_mode.name.lower()))

            if not host in self._specs:
                if os.path.exists(spec_file) and self._append:
                    with open(spec_file, 'r') as f:
                        self._specs[host] = yaml.load(f)
                else:
                    self._specs[host] = BASE_SCHEMA

            self._specs[host] = update_openapi(self._specs[host], reqres, self._update_mode)

            with open(spec_file, 'w') as f:
                yaml.dump(self._specs[host], f)

            logger.debug('Updated scheme for host %s', host)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for f in self._logs.values():
            f.close()
