import json
import logging
import os

from http_types import (
    HttpExchange,
    HttpExchangeWriter,
    Request,
    RequestBuilder,
    Response,
    ResponseBuilder,
)
from openapi_typed_2 import convert_from_openapi, convert_to_openapi

from ...build.builder import BASE_SCHEMA, update_openapi

logger = logging.getLogger(__name__)


class DataCallback:
    def log(self, request: Request, response: Response):
        raise NotImplementedError()


class RequestLoggingCallback:
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
        if host not in self._logs:
            log_file = os.path.join(self._log_dir, "{}-recordings.jsonl".format(host))
            if self._append and os.path.exists(log_file):
                self._logs[host] = open(log_file, "a")
            else:
                self._logs[host] = open(log_file, "w")

        HttpExchangeWriter(self._logs[host]).write(reqres)
        self._logs[host].flush()

        logger.debug("Logs for %s were updated", host)

        if self._update_mode:
            spec_file = os.path.join(
                self._specs_dir,
                "{}_{}.json".format(host, self._update_mode.name.lower()),
            )

            if host not in self._specs:
                if os.path.exists(spec_file) and self._append:
                    with open(spec_file, "r") as f:
                        self._specs[host] = convert_to_openapi(json.load(f))
                else:
                    self._specs[host] = BASE_SCHEMA

            self._specs[host] = update_openapi(
                self._specs[host], reqres, self._update_mode
            )

            with open(spec_file, "w") as f:
                spec = convert_from_openapi(self._specs[host])
                json.dump(spec, f)
                f.flush()

            logger.debug("Schema for %s was updated", host)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for f in self._logs.values():
            f.close()
