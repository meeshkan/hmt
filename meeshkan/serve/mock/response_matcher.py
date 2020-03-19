import json
import logging
import os
import random
from typing import Mapping

import yaml
from faker import Faker
from http_types import Request, Response
from openapi_typed_2 import (
    OpenAPIObject,
    convert_to_openapi,
)

from meeshkan.serve.mock.callbacks import callback_manager
from meeshkan.serve.mock.faker import MeeshkanFaker
from meeshkan.serve.mock.faker.faker_exception import FakerException
from meeshkan.serve.mock.matcher import (
    match_request_to_openapi,
)
from meeshkan.serve.mock.rest import rest_middleware_manager
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

    def _match_response(self, request, name, spec):
        try:
            return MeeshkanFaker(self._text_faker, request, spec, storage_manager[name]).execute()
        except FakerException as e:
            return self.match_error(str(e), request)

    def get_response(self, request: Request) -> Response:
        if request.method.value is None:
            method_error = "Could not find a method %s for path %s on hostname %s." % (
                request.method.value,
                request.path,
                request.host,
            )
            return self.match_error(method_error, request)

        schemas = rest_middleware_manager.spew(request, self._schemas)
        match = match_request_to_openapi(request, schemas)

        if len(match) == 0:
            return callback_manager(request, self.match_error(
                "Could not find a open API schema for the host %s." % request.host,
                request), storage_manager.default)

        name, spec = random.choice(list(match.items()))
        if spec.paths is None or len(spec.paths.items()) == 0:
            path_error = "Could not find a path %s on hostname %s." % (
                request.path,
                request.host,
            )
            return self.match_error(path_error, request)

        response = self._match_response(request, name, spec)
        return callback_manager(request, response, storage_manager[name])
