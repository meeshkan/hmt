########################
#### FAKER
########################
import random
from functools import reduce
from typing import Any

from faker import Faker

fkr = Faker()
__all__ = ["fake_it"]
_LO = -99999999
_HI = 99999999


# to prevent too-nested objects
def sane_depth(n):
    return max([0, 3 - n])


def fake_object(schema: Any, top_schema: Any, depth: int) -> Any:
    addls = (
        {}
        if "additionalProperties" not in schema
        else {
            k: v
            for k, v in [
                (
                    fkr.name(),
                    random.random()
                    if (isinstance(schema["additionalProperties"], bool))
                    and (schema["additionalProperties"] is True)
                    else fake_it(schema["additionalProperties"], top_schema, depth),
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
            : min([sane_depth(depth), random.randint(0, len(properties) - 1)])
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
                (p, fake_it(schema["properties"][p], top_schema, depth))
                for p in properties
            ]
        },
    }


def fake_array(schema: Any, top_schema: Any, depth: int) -> Any:
    mn = 0 if "minItems" not in schema else schema["minItems"]
    mx = 100 if "maxItems" not in schema else schema["maxItems"]
    return (
        []
        if "items" not in schema
        else [fake_it(x, top_schema, depth) for x in schema["items"]]
        if isinstance(schema["items"], list)
        else [
            fake_it(schema["items"], top_schema, depth)
            for x in range(random.randint(mn, mx))
        ]
    )


def fake_any_of(schema: Any, top_schema: Any, depth: int) -> Any:
    return fake_it(random.choice(schema["anyOf"]), top_schema, depth)


def fake_all_of(schema: Any, top_schema: Any, depth: int) -> Any:
    return reduce(
        lambda a, b: {**a, **b},
        [fake_it(x, top_schema, depth) for x in schema["allOf"]],
        {},
    )


def fake_one_of(schema: Any, top_schema: Any, depth: int) -> Any:
    return fake_it(random.choice(schema["oneOf"]), top_schema, depth)


# TODO - make this work
def fake_not(schema: Any, top_schema: Any, depth: int) -> Any:
    return {}


# TODO - make this not suck
def fake_string(schema: Any) -> str:
    return random.choice(schema["enum"]) if "enum" in schema else fkr.name()


def fake_boolean(schema: Any) -> bool:
    return (
        random.choice(schema["enum"])
        if "enum" in schema
        else True
        if random.random() > 0.5
        else False
    )


# TODO: add exclusiveMinimum and exclusiveMaximum
def fake_integer(schema: Any) -> int:
    mn = _LO if "minimum" not in schema else schema["minimum"]
    mx = _HI if "maximum" not in schema else schema["maximum"]
    return random.choice(schema["enum"]) if "enum" in schema else random.randint(mn, mx)


def fake_ref(schema: Any, top_schema, depth):
    name = schema["$ref"].split("/")[2]
    return fake_it(top_schema["definitions"][name], top_schema, depth)


def fake_null(schema: Any) -> None:
    return None


def fake_number(schema: Any) -> float:
    mn = _LO if "minimum" not in schema else schema["minimum"]
    mx = _HI if "maximum" not in schema else schema["maximum"]
    return (
        random.choice(schema["enum"])
        if "enum" in schema
        else (random.random() * (mx - mn)) + mn
    )


def fake_it(schema: Any, top_schema: Any, depth: int) -> Any:
    depth += 1
    return (
        fake_array(schema, top_schema, depth)
        if ("type" in schema) and (schema["type"] == "array")
        else fake_any_of(schema, top_schema, depth)
        if "anyOf" in schema
        else fake_all_of(schema, top_schema, depth)
        if "allOf" in schema
        else fake_one_of(schema, top_schema, depth)
        if "oneOf" in schema
        else fake_not(schema, top_schema, depth)
        if "not" in schema
        else fake_ref(schema, top_schema, depth)
        if "$ref" in schema
        else fake_object(schema, top_schema, depth)
        if ("type" not in schema) or (schema["type"] == "object")
        else fake_string(schema)
        if schema["type"] == "string"
        else fake_integer(schema)
        if schema["type"] == "integer"
        else fake_boolean(schema)
        if schema["type"] == "boolean"
        else fake_null(schema)
        if schema["type"] == "null"
        else fake_number(schema)
        if schema["type"] == "number"
        else {}
    )
