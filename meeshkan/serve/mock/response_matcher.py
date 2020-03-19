import json
import logging
import random
from typing import Mapping, Sequence, Union, cast

from faker import Faker
from http_types import Request, Response
from openapi_typed_2 import Reference, convert_from_openapi

from .faker import fake_it
from .matcher import (
    change_ref,
    change_refs,
    get_response_from_ref,
    match_request_to_openapi,
    ref_name,
)
from .rest import rest_middleware_manager
from .security import match_to_security_schemes
from .specs import OpenAPISpecification

fkr = Faker()


logger = logging.getLogger(__name__)


class ResponseMatcher:
    _specs: Sequence[OpenAPISpecification]

    def __init__(self, specs: Sequence[OpenAPISpecification]):
        self._specs = specs

    def match_error(self, msg: str, req: Request) -> Response:
        return self.default_response(
            "%s. Here is the full request: host=%s, path=%s, method=%s."
            % (msg, req.host, req.path, req.method.value)
        )

    def default_response(self, msg):
        json_resp = {"message": msg}
        return Response(
            statusCode=501,
            body=json.dumps(json_resp),
            bodyAsJson=json_resp,
            headers={},
            timestamp=None,
        )

    def get_response(self, request: Request) -> Response:
        # TODO: tight coupling here
        # try to decouple...
        specs = rest_middleware_manager.spew(request, self._specs)

        logger.debug("Matching to security schemes of %d specs", len(specs))
        maybe_security_response = match_to_security_schemes(
            request, [spec.api for spec in specs]
        )

        if maybe_security_response is not None:
            logger.debug("Matched to security scheme, returning response.")
            return maybe_security_response

        logger.debug("Matching to paths")

        matches = match_request_to_openapi(request, specs)

        logger.debug("Found %d matching specs", len(matches))
        if len(matches) == 0:
            return self.match_error(
                "Could not find an OpenAPI schema for the host %s." % request.host,
                request,
            )

        match = random.choice(matches)

        logger.debug("Proceeding with document title %s", match.api.info.title)

        path_error = "Could not find a path %s on hostname %s." % (
            request.path,
            request.host,
        )

        if match.api.paths is None:
            return self.match_error(path_error, request)
        if len(match.api.paths.items()) == 0:
            return self.match_error(path_error, request)

        path_candidates = [x for x in match.api.paths.values()]

        path_candidate = random.choice(path_candidates)

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

        method_error = "Could not find a method %s for path %s on hostname %s." % (
            request.method.value,
            request.path,
            request.host,
        )

        if method is None:
            return self.match_error(method_error, request)
        responses_error = "While a stub for a specification exists for this endpoint, it contains no responses. That usually means the schema is corrupt or it has been constrained too much (ie asking for a 201 response when it only has 200 and 400)."
        if method.responses is None:
            return self.match_error(responses_error, request)
        potential_responses = [r for r in method.responses.items()]

        if len(potential_responses) == 0:
            return self.match_error(responses_error, request)

        response = random.choice(potential_responses)
        response = potential_responses[0]
        response_1 = response[1]
        response_1 = (
            get_response_from_ref(match.api, ref_name(response_1))
            if isinstance(response_1, Reference)
            else response_1
        )
        if response_1 is None:
            return self.match_error(responses_error, request)
        headers: Mapping[str, Union[str, Sequence[str]]] = {}
        if response_1.headers is not None:
            # TODO: can't handle references yet, need to fix
            headers = (
                {}
            )  # { k: (faker(v['schema'], v['schema'], 0) if 'schema' in v else '***') for k,v in headers.items() }
        statusCode = int(response[0] if response[0] != "default" else 400)
        if (response_1.content is None) or len(response_1.content.items()) == 0:
            return Response(
                statusCode=statusCode,
                body="",
                headers=headers,
                bodyAsJson=None,
                timestamp=None,
            )
        mime_types = response_1.content.keys()
        if "application/json" in mime_types:
            content = response_1.content["application/json"]
            if content.schema is None:
                return self.match_error("Could not find schema", request)
            schema = content.schema
            ct: Mapping[str, Union[str, Sequence[str]]] = {
                "Content-Type": "application/json"
            }
            new_headers: Mapping[str, Union[str, Sequence[str]]] = {**headers, **ct}
            if schema is None:
                return Response(
                    statusCode=statusCode,
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
                        match.api.components.schemas.items()
                        if (match.api.components is not None)
                        and (match.api.components.schemas is not None)
                        else []
                    )
                },
            }
            bodyAsJson = fake_it(to_fake, to_fake, 0)
            return Response(
                statusCode=statusCode,
                body=json.dumps(bodyAsJson),
                bodyAsJson=bodyAsJson,
                headers=new_headers,
                timestamp=None,
            )
        if "text/plain" in mime_types:
            return Response(
                statusCode=statusCode,
                body=fkr.sentence(),
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
