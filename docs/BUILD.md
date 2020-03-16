# Building with Meeshkan

Meeshkan builds OpenAPI specs from two possible sources:
- Other OpenAPI specs
- Recordings of HTTP API traffic serialized in the [`http-types`](https://github.com/meeshkan/http-types) format and written to a [`.jsonl`](https://jsonlines.org) file.

In case one only has an OpenAPI spec and no server recodings, it is not necessary to run Meeshkan build and you can go directly to the [`meeshkan mock`](./MOCK.md) command.

## The meeshkan build command

To build an OpenAPI spec from recorded HTTP API traffic and other OpenAPI specs, use the `meeshkan build` command.

```sh
$ meeshkan build -i my_recoding.jsonl -a my_openapi_spec.yml -o result/
```

The above command will blend `my_recording.jsonl` and `my_openapi_spec.yml` into a unified OpenAPI spec stored in `result/openapi.yml`.

## Gen mode versus replay mode

Meeshkan can build OpenAPI specs in two different modes: `gen` and `replay`.  The default mode is `gen`, and the `-m` flag controls which mode is used.

# gen mode

When `meeshkan build` runs in gen mode, it _infers_ the topology of an OpenAPI spec from recorded server traffic. For example, let's say that https://myapi.com returns the following three JSON objects.

`https://myapi.com/users/3`
```json
{ "id": 3, "name": "Helga" }
```

`https://myapi.com/users/4`
```json
{ "id": 4, "name": "Thor" }
```

`https://myapi.com/users/5`
```json
{ "id": 5, "name": "Sven", "age": 96 }
```

Meeshkan will induce that the schema for a `200` resposne from `GET /uses/{id}` should resemble the following.

```json
{
  "type": "object",
  "properties": {
      "id": { "type": "integer", "minimum": 0 },
      "name": { "type": "string", "x-faker": "name.firstName" },
      "age": { "type": "integer", "minimum": 0, "maximum": 200 },
  },
  "required": ["id", "name"]
}
```

We call this `gen` mode because it can be used to generate synthetic data from types. For example, when testing an API, `meeshkan mock` will serve synthetic data based on this spec.  A user will always have an integer id greater than 0, a name that is a first name, and may have an age between 0 and 200.

# replay mode

Alternatively, `replay` mode will serve back rote fixtures recorded from the API.  Using one of the API calls as above, let's examine the spec that Meeshkan produces in replay mode.

`https://myapi.com/users/3`
```json
{ "id": 3, "name": "Helga" }
```

Meeshkan will build a schema that contains the exact response received as a `200` resposne from `GET /uses/3`.

```json
{
  "type": "object",
  "properties": {
      "id": { "type": "integer", "enum": [0] },
      "name": { "type": "string", "enum": ["Helga"] },
  },
  "required": ["id", "name"]
}
```

## Editing and merging specs

Because Meeshkan writes specs in the OpenAPI format, one can use an OpenAPI manipulation tool or library to edit and blend OpenAPI specs.  We'll show one example using [`openapi_typed_2`](https://github.com/meeshkan/openapi_typed_2) to blend together the paths from two different API specs and write a new spec.

```python
from openapi_typed_2 import convert_to_openapi, convert_from_openapi
import json
from dataclasses import replace
import os

with open('replay/openapi.json', 'r') as replay_file:
    with open('gen/openapi.json', 'r') as gen_file:
        replay = convert_to_openapi(json.loads(replay_file.read()))
        gen = convert_to_openapi(json.loads(gen_file.read()))
        new = replace(replay, paths = { **replay.paths, **gen.paths })
        try:
            os.mkdir('both')
        except: pass # exists
        with open('both/openapi.json', 'w') as both_file:
            both_file.write(json.dumps(convert_from_openapi(new), indent=2))
```
