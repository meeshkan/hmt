# Building with Meeshkan

Meeshkan builds OpenAPI specs from two possible sources:
- Recordings of HTTP API traffic serialized in the [`http-types`](https://github.com/meeshkan/http-types) format and written to a [`.jsonl`](https://jsonlines.org) file
- Other OpenAPI specs

In case one only has an OpenAPI spec and no server recodings, it is not necessary to run Meeshkan build and you can go directly to the [`meeshkan mock`](./MOCK.md) command.

## What's in this document

- [The `meeshkan build` command](#the-meeshkan-build-command)
    - [Building a spec from recorded HTTP API traffic](#building-a-spec-from-recorded-http-api-traffic)
    - [Building a spec from both recorded traffic and other OpenAPI specs](#building-a-spec-from-both-recorded-traffic-and-other-openapi-specs)
- [`gen` vs. `replay` mode](#gen-vs-replay-mode)
    - [`gen` mode](#gen-mode)
    - [`replay` mode](#replay-mode)
- [Editing and merging specs](#editing-and-merging-specs)
- [Next up: Mocking with Meeshkan](#next-up-mocking-with-meeshkan)

## The `meeshkan build` command

⚠️ Before getting started, you should make sure that any recorded HTTP API traffic that you'll use is in the correct format. The `meeshkan build` command expects that recordings are in a single [JSON Lines](http://jsonlines.org/) file and every line should be in the [http-types](https://meeshkan.github.io/http-types/) JSON format.

For an example input file, see [recordings.jsonl](https://github.com/Meeshkan/meeshkan/blob/master/resources/recordings.jsonl). The libraries listed at [http-types](https://meeshkan.github.io/http-types/) can be used to generate input files in your language of choice.

### Building a spec from recorded HTTP API traffic

Once you've ensured that your files are formatted correctly, use the `meeshkan build` command to build an OpenAPI schema from your `.jsonl` file:

```bash
$ meeshkan build --input-file path/to/recordings.jsonl 
```

Optionally, you can also specify an output directory using the `--out` flag followed by the path to this directory. By default, Meeshkan will build the new OpenAPI specifications in the `specs` directory. If you used `meeshkan record` to record your API traffic, the `specs` directory was created automatically. 

> More options for the `meeshkan build` command an be seen by running `meeshkan build --help`.

### Building a spec from both recorded traffic and other OpenAPI specs

To build an OpenAPI spec from recorded HTTP API traffic and other OpenAPI specs, you can use the `meeshkan build` command with a few extra flags:

```
$ pip install meeshkan # if not installed yet
$ meeshkan build --input-file pokeapi.co-recodings.jsonl --initial-openapi-spec my_openapi_spec.yml --out result/
```

The above command specifies recordings from the Pokemon API (`pokeapi.co-recodings.jsonl`) as the input file. Then, it blends those recordings with the designated initial spec (`my_openapi_spec.yml`) to create a unified OpenAPI specification. This specification is stored in `result/openapi.yml`.

Designating an output directory (like with `result/` in the previous example) is optional. By default, Meeshkan will build the new OpenAPI specifications in the `specs` directory. If you used `meeshkan record` to record any API traffic, this `specs` directory was created automatically.

> More options for the `meeshkan build` command an be seen by running `meeshkan build --help`.

## `gen` vs. `replay` mode

Meeshkan can build OpenAPI specs in two different modes: `gen` and `replay`.  The default is `gen`, but you can use the `--mode` flag to control which mode is used.

### `gen` mode

When `meeshkan build` runs in `gen` mode, it _infers_ the topology of an OpenAPI spec from recorded server traffic. For example, let's say that `https://myapi.com` returns the following three JSON objects:

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

Meeshkan will induce that the schema for a `200` response from `GET /uses/{id}` should resemble the following:

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
We call this `gen` mode because it can be used to generate synthetic data from types. For example, when testing an API, `meeshkan mock` will serve synthetic data based on this spec. Using the previous response example, we can see that a user will always have an integer `id` greater than 0, a `name` that is a first name, and may have an `age` between 0 and 200.  

### `replay` mode

Alternatively, `replay` mode will serve back rote fixtures recorded from the API. The following API call, let's examine the spec that Meeshkan produces in `replay` mode.

`https://myapi.com/users/3`
```json
{ "id": 3, "name": "Helga" }
```

Meeshkan will build a schema that contains the exact response received as a `200` response from `GET /uses/3`.

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

<!-- TODO: Mixed mode docs -->

## Editing and merging specs

Because Meeshkan writes specs in the OpenAPI format, you can use an OpenAPI manipulation tool or library to edit and blend OpenAPI specs. 

Let's look at one example using [`openapi_typed_2`](https://github.com/meeshkan/openapi_typed_2) to blend together the paths from two different API specs and then write a new spec.

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

## Next up: Mocking with Meeshkan

Once you've generated an OpenAPI specification with `meeshkan build`, you can use that spec to create a mock server using Meeshkan.

To learn how, visit our [mocking documentation](./docs/MOCK.md).
