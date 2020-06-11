import json
import math
import random
import typing
from dataclasses import dataclass
from functools import reduce
from typing import Any, Mapping, Sequence, Union, cast

import openapi_typed_2
from faker import Faker
from http_types import Request, Response
from openapi_typed_2 import Operation, PathItem, Reference, Schema, convert_from_openapi

from hmt.serve.mock.faker.faker_base import FakerBase
from hmt.serve.mock.faker.faker_exception import FakerException
from hmt.serve.mock.refs import get_response_body
from hmt.serve.mock.request_validation import (
    change_ref,
    change_refs,
    validate_header_params,
    validate_query_params,
)
from hmt.serve.mock.specs import OpenAPISpecification


@dataclass(frozen=True)
class FakerData:
    """
    Common data passed through recursion steps in the StatelessFaker object.
    """

    spec: OpenAPISpecification
    """
    A faked OpenAPI spec
    """
    path_item: str
    """
    A chosen name of PathItem in spec.
    The matcher can return multiple PathItems so we may randomly choose one in the Faker.
    """
    method: Operation
    """
    A chosen http method.
    """
    schema: typing.Dict
    """
    A top-level schema of an http response that is faked.
    It includes all required definitions from spec.
    """
    request: Request
    """
    An incoming http request
    """


class StatelessFaker(FakerBase):
    """
    A stateless implementation of the BaseFaker interface. Generates random data according to a spec. Doesn't use any kind of
    internal states and storages.
    """

    _text_faker: Faker

    _LO = -99999999
    _HI = 99999999

    max_depth = 10

    responses_error = (
        "While a stub for a specification exists for this endpoint, it contains no responses. "
        "That usually means the schema is corrupt or it has been constrained too much "
        "(ie asking for a 201 response when it only has 200 and 400)."
    )

    def __init__(self):
        self._text_faker = Faker()

    def process(
        self, pathname: str, spec: OpenAPISpecification, request: Request,
    ) -> Any:
        path_candidate = spec.api.paths[pathname]

        method = getattr(path_candidate, request.method.value, None)

        if method is None:
            raise FakerException(self.responses_error)

        if method.responses is None or len(method.responses) == 0:
            raise FakerException(self.responses_error)

        status_code, response = self._get_response(
            request, spec, method, path_candidate
        )
        if response is None:
            raise FakerException(self.responses_error)

        headers: Mapping[str, str] = {}
        if response.headers is not None:
            # TODO: can't handle references yet, need to fix
            headers = (
                {}
            )  # { k: (faker(v['schema'], v['schema'], 0) if 'schema' in v else '***') for k,v in headers.items() }
        if (response.content is None) or len(response.content.items()) == 0:
            return self._empty_response(status_code, headers)

        if "application/json" in response.content:
            ct: Mapping[str, str] = {"Content-Type": "application/json"}
            new_headers: Mapping[str, str] = {
                **headers,
                **ct,
            }
            content = response.content["application/json"]
            if content.schema is None:
                return self._empty_response(status_code, new_headers)

            faker_data = FakerData(
                spec=spec,
                path_item=pathname,
                method=method,
                schema=self._build_full_schema(content.schema, spec.definitions),
                request=request,
            )

            return self._fake_json(status_code, new_headers, faker_data)

        elif "text/plain" in response.content:
            return self._fake_text_response(status_code, headers)
        else:
            raise FakerException(
                "Could not produce content for these mime types %s"
                % str(response.content.keys())
            )

    def _get_response(
        self,
        request: Request,
        spec: typing.Optional[OpenAPISpecification],
        method: Operation,
        path_candidate: PathItem,
    ) -> typing.Tuple[int, typing.Optional[openapi_typed_2.Response]]:
        if self._validate_request(
            request, cast(OpenAPISpecification, spec), method, path_candidate
        ):
            for i in range(200, 209):
                code = str(i)
                if code in method.responses:
                    return i, get_response_body(spec.api, method.responses[code])

            status_code, response = random.choice([r for r in method.responses.items()])
            status_code = 400 if status_code == "default" else int(status_code)
            return status_code, get_response_body(spec.api, response)

        else:
            if "default" in method.responses:
                return 400, get_response_body(spec.api, method.responses["default"])
            for i in range(400, 500):
                code = str(i)
                if code in method.responses:
                    return i, get_response_body(spec.api, method.responses[code])

        return 500, None

    def _empty_response(self, status_code: int, headers: typing.Mapping[str, str]):
        return Response(
            statusCode=status_code,
            body="",
            headers=headers,
            bodyAsJson=None,
            timestamp=None,
        )

    def _fake_text_response(self, status_code: int, headers: typing.Mapping[str, str]):
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

    def _fake_json(
        self,
        status_code: int,
        headers: typing.Mapping[str, str],
        faker_data: FakerData,
    ):
        bodyAsJson = self._fake_it(faker_data, faker_data.schema, 0)

        return Response(
            statusCode=status_code,
            body=json.dumps(bodyAsJson),
            bodyAsJson=bodyAsJson,
            headers=headers,
            timestamp=None,
        )

    def _build_full_schema(
        self, schema: typing.Union[Schema, Reference], definitions: typing.Any
    ) -> typing.Dict:
        return {
            **convert_from_openapi(
                change_ref(schema)
                if isinstance(schema, Reference)
                else change_refs(schema)
            ),
            "definitions": definitions,
        }

    def _optional_threshold(self, properties_count, required_count, depth):
        return 0.4 if depth < 3 else 0.4 / math.exp(depth - 2) if depth < 10 else 0

    def _fake_object(self, faker_data: FakerData, schema: Any, depth: int) -> Any:
        addls = (
            {}
            if "additionalProperties" not in schema
            else {
                k: v
                for k, v in [
                    (
                        self._text_faker.name(),
                        random.random()
                        if (isinstance(schema["additionalProperties"], bool))
                        and (schema["additionalProperties"] is True)
                        else self._fake_it(
                            faker_data, schema["additionalProperties"], depth
                        ),
                    )
                    for x in range(random.randint(0, 10))
                ]
            }
        )
        properties = []
        required = set(schema.get("required", []))
        thresh = self._optional_threshold(len(properties), len(required), depth)
        properties = [
            prop
            for prop in schema.get("properties", {}).keys()
            if prop in required or random.random() < thresh
        ]
        random.shuffle(properties)

        return {
            **addls,
            **{
                k: v
                for k, v in [
                    (p, self._fake_it(faker_data, schema["properties"][p], depth))
                    for p in properties
                ]
            },
        }

    def _fake_array(self, faker_data: FakerData, schema: Any, depth: int) -> Any:
        mn = 0 if "minItems" not in schema else schema["minItems"]
        mx = (
            int(100 / math.exp(depth - 1))
            if "maxItems" not in schema
            else schema["maxItems"]
        )
        count = random.randint(mn, mx)

        if "items" not in schema:
            return []
        elif isinstance(schema["items"], list):
            return [self._fake_it(faker_data, x, depth) for x in schema["items"]]
        else:
            items_schema = schema["items"]
            if "$ref" in items_schema:
                return self._fake_ref_array(faker_data, items_schema, depth, count)
            else:
                return [
                    self._fake_it(faker_data, schema["items"], depth)
                    for _ in range(count)
                ]

    def _fake_any_of(self, faker_data: FakerData, schema: Any, depth: int) -> Any:
        return self._fake_it(faker_data, random.choice(schema["anyOf"]), depth)

    def _fake_all_of(self, faker_data: FakerData, schema: Any, depth: int) -> Any:
        return reduce(
            lambda a, b: {**a, **b},
            [self._fake_it(faker_data, x, depth) for x in schema["allOf"]],
            {},
        )

    def _fake_one_of(self, faker_data: FakerData, schema: Any, depth: int) -> Any:
        return self._fake_it(faker_data, random.choice(schema["oneOf"]), depth)

    # TODO - make this work
    def _fake_not(self, faker_data: FakerData, schema: Any, depth: int) -> Any:
        return {}

    # TODO - make this not suck

    def _fake_string(self, schema: Any) -> str:
        return (
            random.choice(schema["enum"])
            if "enum" in schema
            else self._text_faker.name()
        )

    def _fake_boolean(self, schema: Any) -> bool:
        return (
            random.choice(schema["enum"])
            if "enum" in schema
            else True
            if random.random() > 0.5
            else False
        )

    # TODO: add exclusiveMinimum and exclusiveMaximum

    def _fake_integer(self, schema: Any) -> int:
        mn = self._LO if "minimum" not in schema else schema["minimum"]
        mx = self._HI if "maximum" not in schema else schema["maximum"]
        return (
            random.choice(schema["enum"])
            if "enum" in schema
            else random.randint(mn, mx)
        )

    def _fake_ref(self, faker_data: FakerData, schema: Any, depth: int):
        name = schema["$ref"].split("/")[2]
        return self._fake_it(faker_data, faker_data.schema["definitions"][name], depth)

    def _fake_ref_array(
        self, faker_data: FakerData, schema: Any, depth: int, count: int
    ):
        name = schema["$ref"].split("/")[2]
        return [
            self._fake_it(faker_data, faker_data.schema["definitions"][name], depth)
            for _ in range(count)
        ]

    def _fake_null(self) -> None:
        return None

    def _fake_number(self, schema: Any) -> float:
        mn = self._LO if "minimum" not in schema else schema["minimum"]
        mx = self._HI if "maximum" not in schema else schema["maximum"]
        return (
            random.choice(schema["enum"])
            if "enum" in schema
            else (random.random() * (mx - mn)) + mn
        )

    def _fake_it(self, faker_data: FakerData, schema: Any, depth: int) -> Any:
        depth += 1
        return (
            self._fake_array(faker_data, schema, depth)
            if ("type" in schema) and (schema["type"] == "array")
            else self._fake_any_of(faker_data, schema, depth)
            if "anyOf" in schema
            else self._fake_all_of(faker_data, schema, depth)
            if "allOf" in schema
            else self._fake_one_of(faker_data, schema, depth)
            if "oneOf" in schema
            else self._fake_not(faker_data, schema, depth)
            if "not" in schema
            else self._fake_ref(faker_data, schema, depth)
            if "$ref" in schema
            else self._fake_object(faker_data, schema, depth)
            if ("type" not in schema) or (schema["type"] == "object")
            else self._fake_string(schema)
            if schema["type"] == "string"
            else self._fake_integer(schema)
            if schema["type"] == "integer"
            else self._fake_boolean(schema)
            if schema["type"] == "boolean"
            else self._fake_null()
            if schema["type"] == "null"
            else self._fake_number(schema)
            if schema["type"] == "number"
            else {}
        )

    def _validate_request(
        self, request: Request, spec: OpenAPISpecification, op: Operation, p: PathItem,
    ):
        return (
            validate_query_params(request, spec.api, p)
            and validate_header_params(request, spec.api, p)
            # and validate_body(request, spec, op)
        )
