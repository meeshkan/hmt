import copy
import glob
import json
import logging
import os
import yaml
import random
from faker import Faker
from meeshkan.gen.generator import matcher, faker, change_ref, change_refs
fkr = Faker()

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

class MatchError(ValueError): pass

def match_error(msg: str, request: Request):
    return MatchError('%s for path=%s, method=%s' % (msg, request['pathname'], request['method']))

class GeneratedResponseMatcher(ResponseMatcher):
    def __init__(self, schema_dir):
        if not os.path.exists(schema_dir):
            logging.info('OpenAPI schema directory not found %s', schema_dir)
        schemas = [s for s in os.listdir(schema_dir) if s.endswith('yml') or s.endswith('yaml')]
        if len(schemas) > 1:
            logging.info('Multiple schema support not implemented yet - coming soon!')
        if len(schemas) == 0:
            logging.info('Could not find a valid schema. Schemas must have the extension .yaml or .yml.')
        with open(os.path.join(schema_dir, schemas[0]), encoding='utf8') as schema_file:
            self._schema = yaml.safe_load(schema_file.read())


    def get_response(self, request: Request) -> Response:
        # mutate schema to include current hostname in servers
        # this is a hack - should be more versatile than this in future
        if 'servers' not in self._schema:
            self._schema['servers'] = []
        self._schema['servers'].append({'url': '%s://%s' % (request['protocol'], request['host'])})
        match = matcher(request, {'_': self._schema })
        if '_' not in match:
            raise match_error('Could not find a valid OpenAPI schema', request)
        if 'paths' not in match['_']:
            raise match_error('Could not find a valid path', request)
        if len(match['_']['paths'].items()) == 0:
            raise match_error('Could not find a valid path', request)
        if request['method'] not in [x for x in match['_']['paths'].values()][0].keys():
            raise match_error('Could not find the appropriate method', request)
        method = [x for x in match['_']['paths'].values()][0][request['method']]
        if 'responses' not in method:
            raise match_error('Could not find any responses', request)
        potential_responses = [r for r in method['responses'].items()]
        random.shuffle(potential_responses)
        if len(potential_responses) == 0:
            raise match_error('Could not find any responses', request)
        response = potential_responses[0]
        headers = {}
        if 'headers' in response:
            logging.info('Meeshkan cannot generate response headers yet. Coming soon!')
        statusCode = int(response[0] if response[0] != 'default' else 400)
        if ('content' not in response[1]) or len(response[1]['content'].items()) == 0:
            return { 'statusCode': statusCode, 'body': "", 'headers': headers}
        mime_types = response[1]['content'].keys()
        if "application/json" in mime_types:
            content = response[1]['content']['application/json']
            if 'schema' not in content:
                raise match_error('Could not find schema', request)
            schema = content['schema']
            to_fake = {
                **(change_ref(schema) if '$ref' in schema else change_refs(schema)),
                'definitions': { k: change_ref(v) if '$ref' in v else change_refs(v) for k,v in (match['_']['components']['schemas'].items() if '_' in match and 'components' in match['_'] and 'schemas' in match['_']['components'] else [])}
            }
            return {
                'statusCode': statusCode,
                'body': json.dumps(faker(to_fake, to_fake, 0)),
                'headers': { **headers, "Content-Type": "application/json" }
            }
        if "text/plain" in mime_types:
            return {
                'statusCode': statusCode,
                'body': fkr.sentence(),
                'headers': { **headers, "Content-Type": "text/plain" }
            }
        raise match_error('Could not produce content for these mime types %s' % str(mime_types), request)


class MixedResponseMatcher(ResponseMatcher):
    def __init__(self, logs_dir, schema_dir):
        self._replay_matcher = ReplayResponseMatcher(logs_dir)
        self._generated_match = GeneratedResponseMatcher(schema_dir)

    def get_response(self, requst: Request) -> Response:
        pass
