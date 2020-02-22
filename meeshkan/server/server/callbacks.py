import glob
import importlib.util
import inspect
import json
import logging
from dataclasses import replace
import os
from io import StringIO
from http_types import HttpExchange
from http_types.utils import ResponseBuilder, HttpExchangeWriter

from .storage import storage_manager

logger = logging.getLogger(__name__)


class CallbackManager:
    ARGS_MAP_COMMON = {
        'query': lambda request, response, storage: request['query'],
        'request_headers': lambda request, response, storage: request['headers'],
        'respone_headers': lambda request, response, storage: response['headers'],
        'request': lambda request, response, storage: request,
        'response': lambda request, response, storage: response,
        'storage': lambda request, response, storage: storage,
    }

    ARGS_MAP_JSON = {**ARGS_MAP_COMMON,
                     'request_body': lambda request, response, storage: request['bodyAsJson'],
                     'response_body': lambda request, response, storage: response['bodyAsJson']
                     }

    ARGS_MAP_TEXT = {**ARGS_MAP_COMMON,
                     'request_body': lambda request, response, storage: request['body'],
                     'response_body': lambda request, response, storage: response['body']
                     }

    def __init__(self):
        self._callbacks = dict()

    def load(self, path):
        if not os.path.exists(path):
            logger.debug("Callback configuration path doesn't exist %s", path)

        for f in glob.glob(os.path.join(path, '*.py')):
            module_name = 'callbacks.{}'.format(os.path.splitext(os.path.basename(f))[0])
            logging.debug('Loading callbacks from %s to %s module', f, module_name)
            # from https://stackoverflow.com/questions/19009932/import-arbitrary-python-source-file-python-3-3
            spec = importlib.util.spec_from_file_location(module_name, f)
            callbacks = importlib.util.module_from_spec(spec)
            # even though this is an accepted response, the line below
            # triggers a typing error. ignore types for now, but should
            # investigate why the type does not work
            spec.loader.exec_module(callbacks) # type: ignore

        logging.info('Loaded %d callbacks', len(self._callbacks))

    def callback(self, host, method, path):
        return self._callbacks.get((host, method, path))

    def add_callback(self, host, method, path, format, response_type, callback):
        args = inspect.getfullargspec(callback).args
        args_map = self.ARGS_MAP_JSON if format == 'json' else self.ARGS_MAP_TEXT
        self._callbacks[(host, method, path)] = lambda request, response, storage: \
            self._map_results(response, callback(**{arg: args_map[arg](request, response, storage) for arg in args}),
                              format, response_type)

    def _map_results(self, response, result, format, response_type):
        if response_type == 'body':
            if format == 'json':
                response['bodyAsJson'] = result
                response['body'] = json.dumps(result)
            else:
                response['body'] = result
        else:
            if format == 'json':
                response['body'] = json.dumps(result)

        return response

    def __call__(self, request, response):
        callback = self._callbacks.get((request.host, request.method.value, request.pathname))
        if callback is not None:
            sink = StringIO()
            #### there is a bug where sometimes, for unclear reasons,
            #### the request body is sometimes written as a byte string
            #### instead of a string. we hackishly fix here, but note that
            #### the bug exists. would be good to know why
            request = replace(request, body=str(request.body))
            HttpExchangeWriter(sink).write(HttpExchange(request=request, response=response))
            sink.seek(0)
            res = json.loads('\n'.join([x for x in sink]))
            out = callback(res['request'], res['response'], storage_manager.default)
            return ResponseBuilder.from_dict(out)
        else:
            return response


callback_manager = CallbackManager()


def callback(host, method, path, format='json', response='body'):
    def decorator(function):
        callback_manager.add_callback(host, method, path, format, response, function)
        return function
    return decorator





