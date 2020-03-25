import json
import logging
import random
from typing import Sequence

from faker import Faker
from http_types import Request, Response
from meeshkan.serve.mock.callbacks import callback_manager
from meeshkan.serve.mock.faker import MeeshkanFaker
from meeshkan.serve.mock.faker.faker_exception import FakerException
from meeshkan.serve.mock.matcher import (
    match_request_to_openapi,
)
from meeshkan.serve.mock.rest import rest_middleware_manager
from meeshkan.serve.mock.specs import OpenAPISpecification
from meeshkan.serve.mock.data import storage_manager

logger = logging.getLogger(__name__)


class ResponseMatcher:
    _specs: Sequence[OpenAPISpecification]

    def __init__(self, specs: Sequence[OpenAPISpecification]):
        self._specs = specs
        self._fkr = Faker()

        for spec in specs:
            storage_manager.add_mock(spec.source, spec.api)

    def match_error(self, msg: str, req: Request):
        json_resp = {"message": "%s. Here is the full request: host=%s, path=%s, method=%s."
                                % (msg, req.host, req.path, req.method.value)}
        return Response(
            statusCode=501,
            body=json.dumps(json_resp),
            bodyAsJson=json_resp,
            headers={},
            timestamp=None,
        )

    def _match_response(self, request, spec, storage):
        try:
            return MeeshkanFaker(self._fkr, request, spec, storage).execute()
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

        schemas = rest_middleware_manager.spew(request, self._specs)
        match = match_request_to_openapi(request, schemas)

        if len(match) == 0:
            return callback_manager(request, self.match_error(
                "Could not find a open API schema for the host %s." % request.host,
                request), storage_manager.default)

        spec = random.choice(match)
        if spec.api.paths is None or len(spec.api.paths.items()) == 0:
            path_error = "Could not find a path %s on hostname %s." % (
                request.path,
                request.host,
            )
            return self.match_error(path_error, request)

        storage = storage_manager[spec.source]
        response = self._match_response(request, spec.api, storage)
        return callback_manager(request, response, storage)
