########################
#### FAKER
########################
import random
from functools import reduce
from typing import Any

from faker import Faker
from http_types import Request

from meeshkan.serve.mock.faker.faker_base import MeeshkanFakerBase


class MeeshkanSchemaFaker(MeeshkanFakerBase):
    _LO = -99999999
    _HI = 99999999

    def __init__(self):
        self._fkr = Faker()

    # to prevent too-nested objects
    def sane_depth(self, n):
        return max([0, 3 - n])

    def fake_object(self, request: Request, schema: Any, top_schema: Any, depth: int) -> Any:
        addls = (
            {}
            if "additionalProperties" not in schema
            else {
                k: v
                for k, v in [
                    (
                        self._fkr.name(),
                        random.random()
                        if (isinstance(schema["additionalProperties"], bool))
                           and (schema["additionalProperties"] is True)
                        else self.fake_it(request, schema["additionalProperties"], top_schema, depth),
                    )
                    for x in range(random.randint(0, 4))
                ]
            }
        )
        properties = (
            [] if "properties" not in schema else [x for x in schema["properties"].keys()]
        )
        random.shuffle(properties)
        properties = (
            []
            if len(properties) == 0
            else properties[
                 : min([self.sane_depth(depth), random.randint(0, len(properties) - 1)])
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
                    (p, self.fake_it(request, schema["properties"][p], top_schema, depth))
                    for p in properties
                ]
            },
        }

    def fake_array(self, request: Request, schema: Any, top_schema: Any, depth: int) -> Any:
        mn = 0 if "minItems" not in schema else schema["minItems"]
        mx = 100 if "maxItems" not in schema else schema["maxItems"]
        return (
            []
            if "items" not in schema
            else [self.fake_it(request, x, top_schema, depth) for x in schema["items"]]
            if isinstance(schema["items"], list)
            else [
                self.fake_it(request, schema["items"], top_schema, depth)
                for x in range(random.randint(mn, mx))
            ]
        )

    def fake_any_of(self, request: Request, schema: Any, top_schema: Any, depth: int) -> Any:
        return self.fake_it(request, random.choice(schema["anyOf"]), top_schema, depth)

    def fake_all_of(self, request: Request, schema: Any, top_schema: Any, depth: int) -> Any:
        return reduce(
            lambda a, b: {**a, **b},
            [self.fake_it(request, x, top_schema, depth) for x in schema["allOf"]],
            {},
        )

    def fake_one_of(self, request: Request, schema: Any, top_schema: Any, depth: int) -> Any:
        return self.fake_it(request, random.choice(schema["oneOf"]), top_schema, depth)

    # TODO - make this work
    def fake_not(self, request: Request, schema: Any, top_schema: Any, depth: int) -> Any:
        return {}

    # TODO - make this not suck
    def fake_string(self, request: Request, schema: Any) -> str:
        return random.choice(schema["enum"]) if "enum" in schema else self._fkr.name()

    def fake_boolean(self, request: Request, schema: Any) -> bool:
        return (
            random.choice(schema["enum"])
            if "enum" in schema
            else True
            if random.random() > 0.5
            else False
        )

    # TODO: add exclusiveMinimum and exclusiveMaximum
    def fake_integer(self, request: Request, schema: Any) -> int:
        mn = self._LO if "minimum" not in schema else schema["minimum"]
        mx = self._HI if "maximum" not in schema else schema["maximum"]
        return random.choice(schema["enum"]) if "enum" in schema else random.randint(mn, mx)

    def fake_ref(self, request: Request, schema: Any, top_schema, depth):
        name = schema["$ref"].split("/")[2]
        return self.fake_it(request, top_schema["definitions"][name], top_schema, depth)

    def fake_null(self, request: Request, schema: Any) -> None:
        return None

    def fake_number(self, request: Request, schema: Any) -> float:
        mn = self._LO if "minimum" not in schema else schema["minimum"]
        mx = self._HI if "maximum" not in schema else schema["maximum"]
        return (
            random.choice(schema["enum"])
            if "enum" in schema
            else (random.random() * (mx - mn)) + mn
        )

    def fake_it(self, request: Request, schema: Any, top_schema: Any, depth: int) -> Any:
        depth += 1
        return (
            self.fake_array(request, schema, top_schema, depth)
            if ("type" in schema) and (schema["type"] == "array")
            else self.fake_any_of(request, schema, top_schema, depth)
            if "anyOf" in schema
            else self.fake_all_of(request, schema, top_schema, depth)
            if "allOf" in schema
            else self.fake_one_of(request, schema, top_schema, depth)
            if "oneOf" in schema
            else self.fake_not(request, schema, top_schema, depth)
            if "not" in schema
            else self.fake_ref(request, schema, top_schema, depth)
            if "$ref" in schema
            else self.fake_object(request, schema, top_schema, depth)
            if ("type" not in schema) or (schema["type"] == "object")
            else self.fake_string(request, schema)
            if schema["type"] == "string"
            else self.fake_integer(request, schema)
            if schema["type"] == "integer"
            else self.fake_boolean(request, schema)
            if schema["type"] == "boolean"
            else self.fake_null(request, schema)
            if schema["type"] == "null"
            else self.fake_number(request, schema)
            if schema["type"] == "number"
            else {}
        )
