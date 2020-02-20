import json
import logging
import os
import yaml
import random
from faker import Faker
from typing import cast, Mapping, Union, Sequence, Tuple
from openapi_typed import OpenAPIObject, Reference, Schema
from ...gen.generator import matcher, faker, change_ref, change_refs
from http_types import HttpMethod
fkr = Faker()

from http_types import Request, Response

logger = logging.getLogger(__name__)

class ResponseMatcher:
    _schemas: Mapping[str, OpenAPIObject]
    def __init__(self, specs_dir):
        schemas: Sequence[str] = []
        if not os.path.exists(specs_dir):
            logging.info('OpenAPI schema directory not found %s', specs_dir)
        else:
            schemas = [s for s in os.listdir(specs_dir) if s.endswith('yml') or s.endswith('yaml')]
        specs: Sequence[Tuple[str, OpenAPIObject]] = []
        for schema in schemas:
            with open(os.path.join(specs_dir, schema), encoding='utf8') as schema_file:
                # TODO: validate schema?
                specs = [*specs, (schema, cast(OpenAPIObject, yaml.safe_load(schema_file.read())))]
        self._schemas = { k: v for k, v in specs}

    def match_error(self, msg: str, req: Request) -> Response:
        return self.default_response('%s. Here is the full request: host=%s, path=%s, method=%s.' % (msg, req['host'], req['path'], req['method']))

    def default_response(self, msg):
        json_resp = {'message': msg}
        return Response(statusCode=500, body=json.dumps(json_resp), bodyAsJson=json_resp,
                        headers={})


    def get_response(self, request: Request) -> Response:
        # mutate schema to include current hostname in servers
        # this is a hack - should be more versatile than this in future
        match = matcher(request, self._schemas)
        if len(match) == 0:
            return self.match_error('Could not find a open API schema for the host %s.' % request['host'], request)
        match_keys = [x for x in match.keys()]
        random.shuffle(match_keys)
        name = match_keys[0]
        path_error = 'Could not find a path %s on hostname %s.' % (request['path'], request['host'])
        method_error = 'Could not find a method %s for path %s on hostname %s.' % (request['method'], request['path'], request['host'])
        if 'paths' not in match[name]:
            return self.match_error(path_error, request)
        if len(match[name]['paths'].items()) == 0:
            return self.match_error(path_error, request)
        if request['method'] not in [x for x in match[name]['paths'].values()][0].keys():
            return self.match_error(method_error, request)
        method = [x for x in match[name]['paths'].values()][0][cast(HttpMethod, request['method'])]
        responses_error = 'While a stub for a specification exists for this endpoint, it contains no responses. That usually means the schema is corrupt or it has been constrained too much (ie asking for a 201 response when it only has 200 and 400).'
        if 'responses' not in method:
            return self.match_error(responses_error, request)
        potential_responses = [r for r in method['responses'].items()]
        random.shuffle(potential_responses)
        if len(potential_responses) == 0:
            return self.match_error(responses_error, request)
        response = potential_responses[0]
        headers = {}
        if 'headers' in response:
            # TODO: can't handle references yet, need to fix
            headers = {} # { k: (faker(v['schema'], v['schema'], 0) if 'schema' in v else '***') for k,v in headers.items() }
        statusCode = int(response[0] if response[0] != 'default' else 400)
        if ('content' not in response[1]) or len(response[1]['content'].items()) == 0:
            return Response(statusCode=statusCode, body="", headers=headers)
        mime_types = response[1]['content'].keys()
        if "application/json" in mime_types:
            content = response[1]['content']['application/json']
            if 'schema' not in content:
                return self.match_error('Could not find schema', request)
            schema = content['schema']
            to_fake = {
                **(change_ref(schema) if '$ref' in schema else change_refs(schema)),
                'definitions': { k: change_ref(cast(Reference, v)) if '$ref' in v else change_refs(cast(Schema, v)) for k,v in (match[name]['components']['schemas'].items() if name in match and 'components' in match[name] and 'schemas' in match[name]['components'] else [])}
            }
            bodyAsJson = faker(to_fake, to_fake, 0)
            return Response(
                statusCode=statusCode,
                body=json.dumps(bodyAsJson),
                bodyAsJson=bodyAsJson,
                # TODO: can this be accomplished without a cast?
                headers=cast(Mapping[str, Union[str, Sequence[str]]], { **headers, "Content-Type": "application/json" })
            )
        if "text/plain" in mime_types:
            return Response(
                statusCode=statusCode,
                body=fkr.sentence(),
                # TODO: can this be accomplished without a cast?
                headers=cast(Mapping[str, Union[str, Sequence[str]]], { **headers, "Content-Type": "text/plain" })
            )
        return self.match_error('Could not produce content for these mime types %s' % str(mime_types), request)
