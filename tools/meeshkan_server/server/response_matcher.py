import copy
import glob
import json
import logging
import os

from http_types import Request, Response

logger = logging.getLogger(__name__)

class ResponseMatcher:
    def get_response(self, requst: Request) -> Response:
        raise NotImplementedError()

    @property
    def default(self):
        json_resp = {'message': 'Nothing matches your request'}
        return Response(statusCode=500, body=json.dumps(json_resp), bodyAsJson=json_resp,
                        headers={})


class ReplayResponseMatcher(ResponseMatcher):
    def __init__(self, logs_dir):
        self._logs_dir = logs_dir
        if not os.path.exists(self._logs_dir):
            logging.info('Recording logs directory not found %s', logs_dir)

        self._recordings = dict()
        for file in glob.glob(os.path.join(logs_dir, '*.jsonl')):
            host = os.path.splitext(os.path.basename(file))[0]
            with open(file) as f:
                self._recordings[host] = [json.loads(line) for line in f.readlines()]

            logger.debug('Loaded %d recordings for %s', len(self._recordings[host]), host)

    def get_response(self, request: Request) -> Response:
        if request['host'] in self._recordings:
            host_recordings = self._recordings[request['host']]
            suitable = [x for x in host_recordings
                        if x['request']['method'] == request['method'] and
                        x['request']['pathname'] == request['pathname']]
            default = suitable[0]['response'] if len(suitable) > 0 else self.default
            return copy.deepcopy(next((x['response'] for x in suitable if self._exact_match(x['request'], request)), default))
        else:
            return self.default


    def _exact_match(self, recording, real):
        if recording['method'] != real['method']:
            return False

        if recording['pathname'] != real['pathname']:
            return False

        if recording['query'] != real['query']:
            return False

        if recording['bodyAsJson'] != real['bodyAsJson']:
            return False

        return True



class GeneratedResponseMatcher(ResponseMatcher):
    def __init__(self, schema_dir):
        self._logs_dir = schema_dir
        if not os.path.exists(self._logs_dir):
            logging.info('OpenAPI schema directory not found %s', schema_dir)

    def get_response(self, requst: Request) -> Response:
        pass


class MixedResponseMatcher(ResponseMatcher):
    def __init__(self, logs_dir, schema_dir):
        self._replay_matcher = ReplayResponseMatcher(logs_dir)
        self._generated_match = GeneratedResponseMatcher(schema_dir)

    def get_response(self, requst: Request) -> Response:
        pass
