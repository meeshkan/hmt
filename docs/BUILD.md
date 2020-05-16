# Building with HMT

HMT builds OpenAPI specs from two possible sources:
- Recordings of HTTP API traffic serialized in the [`http-types`](https://github.com/hmt/http-types) format and written to a [`.jsonl`](https://jsonlines.org) file
- Other OpenAPI specs

In case one only has an OpenAPI spec and no server recodings, it is not necessary to run HMT build and you can go directly to the [`hmt mock`](./MOCK.md) command.

## What's in this document

- [The `hmt build` command](#the-hmt-build-command)
    - [Building a spec from recorded HTTP API traffic](#building-a-spec-from-recorded-http-api-traffic)
    - [Building a spec from both recorded traffic and other OpenAPI specs](#building-a-spec-from-both-recorded-traffic-and-other-openapi-specs)
- [`gen` vs. `replay` mode](#gen-vs-replay-mode)
    - [`gen` mode](#gen-mode)
    - [`replay` mode](#replay-mode)
- [Editing and merging specs](#editing-and-merging-specs)
- [Next up: Mocking with HMT](#next-up-mocking-with-hmt)

## The `hmt build` command

⚠️ Before getting started, you should make sure that any recorded HTTP API traffic that you'll use is in the correct format. The `hmt build` command expects that recordings are in a single [JSON Lines](http://jsonlines.org/) file and every line should be in the [http-types](https://hmt.github.io/http-types/) JSON format.

For an example input file, see [recordings.jsonl](https://github.com/HMT/hmt/blob/master/resources/recordings.jsonl). The libraries listed at [http-types](https://hmt.github.io/http-types/) can be used to generate input files in your language of choice.

### Building a spec from recorded HTTP API traffic

Once you've ensured that your files are formatted correctly, use the `hmt build` command to build an OpenAPI schema from your `.jsonl` file:

```bash
$ hmt build --input-file path/to/recordings.jsonl 
```

Optionally, you can also specify an output directory using the `--out` flag followed by the path to this directory. By default, HMT will build the new OpenAPI specifications in the `specs` directory. If you used `hmt record` to record your API traffic, the `specs` directory was created automatically. 

> More options for the `hmt build` command an be seen by running `hmt build --help`.

### Building a spec from both recorded traffic and other OpenAPI specs

To build an OpenAPI spec from recorded HTTP API traffic and other OpenAPI specs, you can use the `hmt build` command with a few extra flags:

```
$ pip install hmt # if not installed yet
$ hmt build --input-file pokeapi.co-recodings.jsonl --initial-openapi-spec my_openapi_spec.yml --out result/
```

The above command specifies recordings from the Pokemon API (`pokeapi.co-recodings.jsonl`) as the input file. Then, it blends those recordings with the designated initial spec (`my_openapi_spec.yml`) to create a unified OpenAPI specification. This specification is stored in `result/openapi.yml`.

Designating an output directory (like with `result/` in the previous example) is optional. By default, HMT will build the new OpenAPI specifications in the `specs` directory. If you used `hmt record` to record any API traffic, this `specs` directory was created automatically.

> More options for the `hmt build` command an be seen by running `hmt build --help`.

## `gen` vs. `replay` mode

HMT can build OpenAPI specs in two different modes: `gen` and `replay`.  The default is `gen`, but you can use the `--mode` flag to control which mode is used.

### `gen` mode

When `hmt build` runs in `gen` mode, it _infers_ the topology of an OpenAPI spec from recorded server traffic. For example, let's say that `https://myapi.com` returns the following three JSON objects:

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

HMT will induce that the schema for a `200` response from `GET /uses/{id}` should resemble the following:

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
We call this `gen` mode because it can be used to generate synthetic data from types. For example, when testing an API, `hmt mock` will serve synthetic data based on this spec. Using the previous response example, we can see that a user will always have an integer `id` greater than 0, a `name` that is a first name, and may have an `age` between 0 and 200.  

### `replay` mode

Alternatively, `replay` mode will serve back rote fixtures recorded from the API. The following API call, let's examine the spec that HMT produces in `replay` mode.

`https://myapi.com/users/3`
```json
{ "id": 3, "name": "Helga" }
```

HMT will build a schema that contains the exact response received as a `200` response from `GET /uses/3`.

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

Because HMT writes specs in the OpenAPI format, you can use an OpenAPI manipulation tool or library to edit and blend OpenAPI specs. 

Let's look at one example using [`openapi_typed_2`](https://github.com/meeshkan/openapi-typed-2) to blend together the paths from two different API specs and then write a new spec.

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

## Next up: Mocking with HMT

Once you've generated an OpenAPI specification with `hmt build`, you can use that spec to create a mock server using HMT.

To learn how, visit our [mocking documentation](./docs/MOCK.md).
