import json
import random
import typing
from dataclasses import dataclass
from functools import reduce
from typing import Any, Mapping, Sequence, Union, cast

from faker import Faker
from http_types import Request, Response
from openapi_typed_2 import (
    OpenAPIObject,
    Operation,
    Reference,
    Schema,
    convert_from_openapi,
)

from hmt.serve.mock.faker.faker_base import FakerBase
from hmt.serve.mock.faker.faker_exception import FakerException
from hmt.serve.mock.matcher import (
    change_ref,
    change_refs,
    get_response_from_ref,
    ref_name,
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

    responses_error = (
        "While a stub for a specification exists for this endpoint, it contains no responses. "
        "That usually means the schema is corrupt or it has been constrained too much "
        "(ie asking for a 201 response when it only has 200 and 400)."
    )

    def __init__(self):
        self._text_faker = Faker()

    def process(self, spec: OpenAPISpecification, request: Request) -> Any:
        path_item, path_candidate = random.choice([x for x in spec.api.paths.items()])

        method = getattr(path_candidate, request.method.value, None)

        if method is None:
            raise FakerException(self.responses_error)

        if method.responses is None or len(method.responses) == 0:
            raise FakerException(self.responses_error)

        status_code, response = random.choice([r for r in method.responses.items()])
        status_code = int(status_code if status_code != "default" else 400)

        response = (
            get_response_from_ref(spec.api, ref_name(response))
            if isinstance(response, Reference)
            else response
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
                path_item=path_item,
                method=method,
                schema=self._build_full_schema(content.schema, spec.api),
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
        self, status_code: int, headers: typing.Mapping[str, str], faker_data: FakerData
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
        self, schema: typing.Union[Schema, Reference], spec: OpenAPIObject
    ) -> typing.Dict:
        return {
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
                    if (spec.components is not None)
                    and (spec.components.schemas is not None)
                    else []
                )
            },
        }

    # to prevent too-nested objects
    def _sane_depth(self, n):
        return max([0, 3 - n])

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
                    for x in range(random.randint(0, 4))
                ]
            }
        )
        properties = list(schema.get("properties", {}).keys())
        random.shuffle(properties)
        properties = (
            []
            if len(properties) == 0
            else properties[
                : min([self._sane_depth(depth), random.randint(0, len(properties) - 1)])
            ]
        )
        properties = list(
            set(([] if "required" not in schema else schema["required"]) + properties)
        )
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
        mx = 100 if "maxItems" not in schema else schema["maxItems"]
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

    def _fake_null(self, schema: Any) -> None:
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
            else self._fake_null(schema)
            if schema["type"] == "null"
            else self._fake_number(schema)
            if schema["type"] == "number"
            else {}
        )
