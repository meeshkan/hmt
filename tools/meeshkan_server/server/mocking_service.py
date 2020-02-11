import json
import logging
import importlib.util

from http_types import Request, Response
from tools.meeshkan_server.server.decorators import callback_dict

logger = logging.getLogger(__name__)

class MockingService:
    def __init__(self, log_dir, schema_dir, callback_path):
        self._log_dir = log_dir
        self._schema_dir = schema_dir
        spec = importlib.util.spec_from_file_location("callbacks", callback_path)
        callbacks = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(callbacks)
        self._storage = dict()


    def match(self, request: Request) -> Response:
        logger.debug(request)
        json_resp = {'message': 'Hello mocked world!'}
        resp = Response(statusCode=200, body=json.dumps(json_resp), bodyAsJson=json_resp,
                        headers={})
        callback = callback_dict.get_callback(request['host'], request['method'], request['pathname'])
        if callback is not None:
            return callback(request, resp, self._storage)
        else:
            return resp

