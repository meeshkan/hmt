import json
import logging
import typing
from typing import Sequence

from http_types import Request, Response

from hmt.serve.mock.callbacks import CallbackManager
from hmt.serve.mock.faker.faker_exception import FakerException
from hmt.serve.mock.faker.stateful_faker import StatefulFaker
from hmt.serve.mock.matcher import match_request_to_openapi
from hmt.serve.mock.rest import RestMiddlewareManager
from hmt.serve.mock.security import match_to_security_schemes
from hmt.serve.mock.specs import OpenAPISpecification
from hmt.serve.mock.storage.mock_data_store import MockDataStore

logger = logging.getLogger(__name__)


class RequestProcessor:
    _specs: Sequence[OpenAPISpecification]

    def __init__(
        self,
        specs: Sequence[OpenAPISpecification],
        mock_data_store: MockDataStore,
        callback_manager: CallbackManager,
        rest_middleware_manager: RestMiddlewareManager,
    ):
        self._specs = specs
        self._mock_data_store = mock_data_store
        self._callback_manager = callback_manager
        self._rest_middleware_manager = rest_middleware_manager
        self._faker = StatefulFaker(self._mock_data_store)

    def match_error(self, msg: str, req: Request):
        json_resp = {
            "message": "%s. Here is the full request: host=%s, path=%s, method=%s."
            % (msg, req.host, req.path, req.method.value)
        }
        return Response(
            statusCode=501,
            body=json.dumps(json_resp),
            bodyAsJson=json_resp,
            headers={},
            timestamp=None,
        )

    def _match_response(
        self, pathname: str, spec: OpenAPISpecification, request: Request,
    ):
        try:
            return self._faker.process(pathname, spec, request)
        except FakerException as e:
            return self.match_error(str(e), request)

    def process(self, request: Request) -> Response:
        if request.method.value is None:
            method_error = "Could not find a method %s for path %s on hostname %s." % (
                request.method.value,
                request.path,
                request.host,
            )
            return self.match_error(method_error, request)

        specs = self._rest_middleware_manager.spew(request, self._specs)

        logger.debug("Matching to security schemes of %d specs", len(specs))
        maybe_security_response = match_to_security_schemes(
            request, [spec.api for spec in specs]
        )

        if maybe_security_response is not None:
            return maybe_security_response

        pathname, spec = match_request_to_openapi(request, specs)

        if pathname is None:
            return self._callback_manager(
                request,
                self.match_error(
                    "Could not find an open API schema for the host {} and the path {}".format(
                        request.host, request.path
                    ),
                    request,
                ),
                self._mock_data_store.default,
            )

        storage = self._mock_data_store[spec.source]
        response = self._match_response(
            pathname, typing.cast(OpenAPISpecification, spec), request
        )
        return self._callback_manager(request, response, storage)
