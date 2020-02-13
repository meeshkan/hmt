from meeshkan.gen.generator import faker, valid_schema
import jsonschema

def test_faker_1():
    schema = {
  "type": "array",
  "items": {
    "type": "object",
    "required": [
      "foo",
      "baz"
    ],
    "properties": {
      "foo": {
        "type": "number"
      },
      "bar": {
        "type": "string"
      },
      "baz": {
        "type": "string"
      }
    }
  }
}
    res = faker(schema, schema)
    assert valid_schema(res, schema)
