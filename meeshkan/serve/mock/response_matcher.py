import json
import logging

from meeshkan.serve.mock.callbacks import callback_manager
from meeshkan.serve.mock.faker import MeeshkanFaker
from meeshkan.serve.mock.rest import rest_middleware_manager
import os
import yaml
import random
from faker import Faker
from typing import cast, Mapping, Union, Sequence, Tuple
from openapi_typed_2 import (
    convert_from_openapi,
    OpenAPIObject,
    Reference,
    convert_to_openapi,
)
from meeshkan.serve.mock.matcher import (
    get_response_from_ref,
    match_request_to_openapi,
    change_ref,
    change_refs,
    ref_name,
)

from http_types import Request, Response

from meeshkan.serve.mock.storage import storage_manager

logger = logging.getLogger(__name__)


class ResponseMatcher:
    _schemas: Mapping[str, OpenAPIObject]

    def __init__(self, specs_dir):
        self._text_faker = Faker()
        self._schemas = {}
        if not os.path.exists(specs_dir):
            logging.info("OpenAPI schema directory not found %s", specs_dir)
        else:
            schemas = (
                s
                for s in os.listdir(specs_dir)
                if s.endswith("yml") or s.endswith("yaml") or s.endswith("json")
            )
            for schema in schemas:
                with open(os.path.join(specs_dir, schema), encoding="utf8") as schema_file:
                    dict_spec = (json.loads if schema.endswith("json") else yaml.safe_load)(schema_file.read())
                    spec = convert_to_openapi(dict_spec)
                    storage_manager.add_mock(schema, spec)
                    self._schemas[schema] = spec


    def match_error(self, msg: str, req: Request) -> Response:
        return self.default_response(
            "%s. Here is the full request: host=%s, path=%s, method=%s."
            % (msg, req.host, req.path, req.method.value)
        )

    def default_response(self, msg):
        json_resp = {"message": msg}
        return Response(
            statusCode=500,
            body=json.dumps(json_resp),
            bodyAsJson=json_resp,
            headers={},
            timestamp=None,
        )

    def _match_response(self, request, name, spec, match):
        path_error = "Could not find a path %s on hostname %s." % (
            request.path,
            request.host,
        )
        method_error = "Could not find a method %s for path %s on hostname %s." % (
            request.method.value,
            request.path,
            request.host,
        )

        if spec.paths is None:
            return self.match_error(path_error, request)
        if len(spec.paths.items()) == 0:
            return self.match_error(path_error, request)
        path_candidates = [x for x in spec.paths.values()]
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
        responses_error = "While a stub for a specification exists for this endpoint, it contains no responses. That usually means the schema is corrupt or it has been constrained too much (ie asking for a 201 response when it only has 200 and 400)."
        if method.responses is None or len(method.responses) == 0:
            return self.match_error(responses_error, request)
        status_code, response = random.choice([r for r in method.responses.items()])
        status_code = int(status_code if status_code != "default" else 400)

        response = (
            get_response_from_ref(spec, ref_name(response))
            if isinstance(response, Reference)
            else response
        )
        if response is None:
            return self.match_error(responses_error, request)
        headers: Mapping[str, Union[str, Sequence[str]]] = {}
        if response.headers is not None:
            # TODO: can't handle references yet, need to fix
            headers = (
                {}
            )  # { k: (faker(v['schema'], v['schema'], 0) if 'schema' in v else '***') for k,v in headers.items() }
        if (response.content is None) or len(response.content.items()) == 0:
            return Response(
                statusCode=status_code,
                body="",
                headers=headers,
                bodyAsJson=None,
                timestamp=None,
            )
        mime_types = response.content.keys()
        if "application/json" in mime_types:
            content = response.content["application/json"]
            if content.schema is None:
                return self.match_error("Could not find schema", request)
            schema = content.schema
            ct: Mapping[str, Union[str, Sequence[str]]] = {
                "Content-Type": "application/json"
            }
            new_headers: Mapping[str, Union[str, Sequence[str]]] = {**headers, **ct}
            if schema is None:
                return Response(
                    statusCode=status_code,
                    body="",
                    bodyAsJson="",
                    headers=new_headers,
                    timestamp=None,
                )
            to_fake = {
                **convert_from_openapi(
                    change_ref(schema)
                    if isinstance(schema, Reference)
                    else change_refs(schema)
                ),
                "definitions": {
                    k: convert_from_openapi(
                        change_ref(v) if isinstance(v, Reference) else change_refs(v)
                    )
                    for k, v in (
                        spec.components.schemas.items()
                        if (name in match)
                        and (spec.components is not None)
                        and (spec.components.schemas is not None)
                        else []
                    )
                },
            }
            bodyAsJson = self._json_faker.fake_it(request, to_fake, to_fake, 0)
            return Response(
                statusCode=status_code,
                body=json.dumps(bodyAsJson),
                bodyAsJson=bodyAsJson,
                headers=new_headers,
                timestamp=None,
            )
        if "text/plain" in mime_types:
            return Response(
                statusCode=status_code,
                body=self._text_faker.sentence(),
                # TODO: can this be accomplished without a cast?
                headers=cast(
                    Mapping[str, Union[str, Sequence[str]]],
                    {**headers, "Content-Type": "text/plain"},
                ),
                bodyAsJson=None,
                timestamp=None,
            )
        return self.match_error(
            "Could not produce content for these mime types %s" % str(mime_types),
            request,
        )

    def get_response(self, request: Request) -> Response:
        # TODO: tight coupling here
        # try to decouple...
        schemas = rest_middleware_manager.spew(request, self._schemas)
        match = match_request_to_openapi(request, schemas)

        if len(match) == 0:
            return callback_manager(request, self.match_error(
                "Could not find a open API schema for the host %s." % request.host,
                request), storage_manager.default)

        name, spec = random.choice(list(match.items()))
        response = self._match_response(request, name, spec, match)
        return callback_manager(request, response, storage_manager[name])
