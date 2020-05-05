import json

from hamcrest import *

from hmt.build.json_schema import to_json_schema, to_openapi_json_schema
from hmt.build.update_mode import UpdateMode

from ..util import read_recordings_as_dict

request_samples = read_recordings_as_dict()
object_sample = json.loads(request_samples[0]["response"]["body"])


test_objects = [[{"fork": True}], [{}]]


def test_to_schema_from_array():
    schema = to_json_schema(object_sample, UpdateMode.GEN, schema=None)
    assert_that(schema, has_key("$schema"))
    assert_that(
        schema, has_entry("$schema", starts_with("http://json-schema.org/schema#"))
    )
    assert_that(schema, has_entry("type", "array"))
    assert_that(schema, has_entry("items", instance_of(dict)))


def test_schema_with_array():
    schema = to_json_schema(test_objects[0], UpdateMode.GEN, schema=None)
    assert_that(schema, has_entry("items", instance_of(dict)))
    items = schema["items"]
    assert isinstance(items, dict)  # typeguard
    assert_that(items, has_entry("required", ["fork"]))
    assert_that(items, has_entry("properties", instance_of(dict)))
    properties = items["properties"]
    assert_that(properties, has_entries(fork=instance_of(dict)))
    forks = properties["fork"]
    assert_that(forks, has_entries(type="boolean"))


def test_updating_schema_removes_required():
    schema = to_json_schema(test_objects[0], UpdateMode.GEN, schema=None)
    schema = to_json_schema(test_objects[1], UpdateMode.GEN, schema=schema)
    items = schema["items"]
    assert isinstance(items, dict)  # typeguard
    assert_that(items, any_of(is_not(has_key("required")), has_entry("required", [])))
    assert_that(items, has_entry("properties", has_key("fork")))


def test_openapi_compatible_schema():
    schema = to_openapi_json_schema(test_objects[0], UpdateMode.GEN, schema=None)
    assert_that(schema, not_(has_key("$schema")))
