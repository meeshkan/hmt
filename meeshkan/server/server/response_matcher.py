import json
import logging
from meeshkan.server.server.rest import rest_middleware_manager
import os
import yaml
import random
from faker import Faker
from typing import cast, Mapping, Union, Sequence, Tuple
from openapi_typed_2 import convert_from_openapi, OpenAPIObject, Reference, Schema, convert_to_openapi
from ...gen.generator import get_response_from_ref, matcher, faker, change_ref, change_refs, ref_name
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
            schemas = [s for s in os.listdir(specs_dir) if s.endswith('yml') or s.endswith('yaml') or s.endswith('json')]
        specs: Sequence[Tuple[str, OpenAPIObject]] = []
        for schema in schemas:
            with open(os.path.join(specs_dir, schema), encoding='utf8') as schema_file:
                # TODO: validate schema?
                specs = [*specs, (schema, convert_to_openapi((json.loads if schema.endswith('json') else yaml.safe_load)(schema_file.read())))]
        self._schemas = { k: v for k, v in specs}

    def match_error(self, msg: str, req: Request) -> Response:
        return self.default_response('%s. Here is the full request: host=%s, path=%s, method=%s.' % (msg, req.host, req.path, req.method.value))

    def default_response(self, msg):
        json_resp = {'message': msg}
        return Response(statusCode=500, body=json.dumps(json_resp), bodyAsJson=json_resp,
                        headers={}, timestamp=None)


    def get_response(self, request: Request) -> Response:
        # TODO: tight coupling here
        # try to decouple...
        schemas = rest_middleware_manager.spew(request, self._schemas)
        match = matcher(request, schemas)
        if len(match) == 0:
            return self.match_error('Could not find a open API schema for the host %s.' % request.host, request)
        match_keys = [x for x in match.keys()]
        random.shuffle(match_keys)
        name = match_keys[0]
        path_error = 'Could not find a path %s on hostname %s.' % (request.path, request.host)
        method_error = 'Could not find a method %s for path %s on hostname %s.' % (request.method.value, request.path, request.host)
        if match[name].paths is None:
            return self.match_error(path_error, request)
        if len(match[name].paths.items()) == 0:
            return self.match_error(path_error, request)
        path_candidates = [x for x in match[name].paths.values()]
        random.shuffle(path_candidates)
        path_candidate = path_candidates[0]
        method = {
            "get": path_candidate.get,
            "post": path_candidate.post,
            "put": path_candidate.put,
            "delete": path_candidate.delete,
            "options": path_candidate.options,
            "head": path_candidate.head,
            "patch": path_candidate.patch,
            "trace": path_candidate.trace,
        }.get(str(request.method.value), None)
        if request.method.value is None:
            return self.match_error(method_error, request)
        responses_error = 'While a stub for a specification exists for this endpoint, it contains no responses. That usually means the schema is corrupt or it has been constrained too much (ie asking for a 201 response when it only has 200 and 400).'
        if method.responses is None:
            return self.match_error(responses_error, request)
        potential_responses = [r for r in method.responses.items()]
        random.shuffle(potential_responses)
        if len(potential_responses) == 0:
            return self.match_error(responses_error, request)
        response = potential_responses[0]
        response_1 = response[1]
        response_1 = get_response_from_ref(match[name], ref_name(response_1)) if isinstance(response_1, Reference) else response_1
        if response_1 is None:
            return self.match_error(responses_error, request)
        headers: Mapping[str, Union[str, Sequence[str]]] = {}
        if response_1.headers is not None:
            # TODO: can't handle references yet, need to fix
            headers = {} # { k: (faker(v['schema'], v['schema'], 0) if 'schema' in v else '***') for k,v in headers.items() }
        statusCode = int(response[0] if response[0] != 'default' else 400)
        if (response_1.content is None) or len(response_1.content.items()) == 0:
            return Response(statusCode=statusCode, body="", headers=headers, bodyAsJson=None, timestamp=None)
        mime_types = response_1.content.keys()
        if "application/json" in mime_types:
            content = response_1.content['application/json']
            if content.schema is None:
                return self.match_error('Could not find schema', request)
            schema = content.schema
            ct: Mapping[str, Union[str, Sequence[str]]] = { "Content-Type": "application/json" }
            new_headers: Mapping[str, Union[str, Sequence[str]]] = { **headers, **ct }
            if schema is None:
                return Response(
                    statusCode=statusCode,
                    body="",
                    bodyAsJson="",
                    headers=new_headers,
                    timestamp=None
                )
            to_fake = {
                **convert_from_openapi(change_ref(schema) if isinstance(schema, Reference) else change_refs(schema)),
                'definitions': { k: convert_from_openapi(change_ref(v) if isinstance(v, Reference) else change_refs(v)) for k,v in (match[name].components.schemas.items() if (name in match) and (match[name].components is not None) and (match[name].components.schemas is not None) else [])}
            }
            bodyAsJson = faker(to_fake, to_fake, 0)
            return Response(
                statusCode=statusCode,
                body=json.dumps(bodyAsJson),
                bodyAsJson=bodyAsJson,
                headers=new_headers,
                timestamp=None
            )
        if "text/plain" in mime_types:
            return Response(
                statusCode=statusCode,
                body=fkr.sentence(),
                # TODO: can this be accomplished without a cast?
                headers=cast(Mapping[str, Union[str, Sequence[str]]], { **headers, "Content-Type": "text/plain" }),
                bodyAsJson=None,
                timestamp=None
            )
        return self.match_error('Could not produce content for these mime types %s' % str(mime_types), request)
