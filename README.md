# Meeshkan

[![CircleCI](https://circleci.com/gh/meeshkan/meeshkan.svg?style=shield)](https://circleci.com/gh/meeshkan/meeshkan)
[![PyPI](https://img.shields.io/pypi/dm/meeshkan.svg)](https://pypi.org/project/meeshkan/)
[![PyPi](https://img.shields.io/pypi/pyversions/meeshkan)](https://pypi.org/project/meeshkan/)
[![License](https://img.shields.io/pypi/l/meeshkan)](LICENSE)

Meeshkan is a tool for mocking HTTP APIs for use in sandboxes as well as for automated and exploratory testing. It uses a combination of API definitions, recorded traffic and code in order to make crafting mocks as enjoyable as possible.

Meeshkan requires Python 3.6 or later.

## Table of Contents

1. [Installation](#installation)
1. [Python API](#python-api)
1. [Builder](#builder)
1. [Mocking](#mocking)
1. [Recording](#recording)
1. [Converting](#converting)
1. [Development](#development)
1. [Contributing](#contributing)

## Installation

Install via [pip](https://pip.pypa.io/en/stable/installing/):

```bash
$ pip install meeshkan
```

Note that `meeshkan` requires **Python 3.6+.**

## Python API

### Quick start

```python
from meeshkan.schemabuilder.update_mode import UpdateMode
from meeshkan.schemabuilder import build_schema_batch, build_schema_online, update_openapi
from openapi_typed_2 import OpenAPIObject
import meeshkan
from typing import List
import json
from http_types import HttpExchange, Request, Response, ResponseBuilder, RequestBuilder, HttpMethod


def read_http_exchanges() -> List[HttpExchange]:
    """Read HTTP exchanges from the source of your choice.
    """
    request: Request = RequestBuilder.from_url(
        "https://example.org/v1", method=HttpMethod.GET, headers={})

    response: Response = ResponseBuilder.from_dict(dict(
        statusCode=200, body=json.dumps({"hello": "world"}), headers={}))

    http_exchange: HttpExchange = HttpExchange(request=request, response=response)

    return [http_exchange]


http_exchanges = read_http_exchanges()

# Build OpenAPI schema from a list of recordings
openapi: OpenAPIObject = build_schema_batch(http_exchanges)

# Build schema from an iterator
openapi: OpenAPIObject = build_schema_online(iter(http_exchanges), UpdateMode.GEN)

# Update OpenAPI schema one `HttpExchange` at a time
http_exchange = http_exchanges[0]
openapi: OpenAPIObject = update_openapi(openapi, http_exchange, UpdateMode.GEN)
```

## Builder

Using the Meeshkan CLI, you can build OpenAPI schema from a single `recordings.jsonl` file in the [HTTP Types](https://meeshkan.github.io/http-types/) JSON format.

```bash
$ pip install meeshkan # if not done yet
$ meeshkan build --source file -i path/to/recordings.jsonl [-o path/to/output_directory]
```

The input file should be in [JSON Lines](http://jsonlines.org/) format and every line should be in [HTTP Types](https://meeshkan.github.io/http-types/) JSON format.For an example input file, see [recordings.jsonl](https://github.com/Meeshkan/meeshkan/blob/master/resources/recordings.jsonl). The libraries listed at [HTTP Types](https://meeshkan.github.io/http-types/) can be used to generate input files in your language of choice.

Use dash (`-i -`) to read from standard input:

```bash
$ meeshkan build --source file -i - < recordings.jsonl
```

### Building modes

You can use a mode flag to indicate how the OpenAPI spec should be built, ie:

```bash
meeshkan build --mode gen -i path/to/recordings.jsonl
```

Supported modes are:

- gen [default] - infer a schema from the recorded data
- replay - replay the recorded data based on exact matching
- mixed - replay the recorded data based on exact matching when it is possible

The OpenAPI schemas can be manually edited to mix the two modes.

### Reading from Kafka

Set `--source kafka` in `build` command:

```bash
$ meeshkan build --source kafka [-o path/to/output_directory]
```

_TODO: Configuration for Kafka_

## Mocking

You can use an existing OpenAPI spec, an OpenAPI spec you've built using `meeshkan build`, and recordings to create a mock server using Meeshkan.

```bash
$ pip install meeshkan # if not installed yet
$ meeshkan mock
```

### Common command-line arguments

The following commands are available in mock mode:

| Argument     | Description                                                                                                            | Default |
| ------------ | ---------------------------------------------------------------------------------------------------------------------- | ------- |
| `port`       | Server port                                                                                                            | 8000    |
| `admin_port` | Admin port                                                                                                             | 8999    |
| `log_dir`    | The directory containing `.jsonl` files for mocking directly from recorded fixtures                                    | `logs`  |
| `specs_dir`  | The directory containing `.yml` or `.yaml` OpenAPI specs used for mocking, including ones built using `meeshkan build` | `specs` |

## Recording

In addition to the builder, Meeshkan provides a recorder that can capture API traffic using a proxy and, like the builder, automatically assembles it into an OpenAPI schema in addition to storing the raw recordings.

```bash
$ pip install meeshkan # if not installed yet
$ meeshkan record
```

This starts Meeshkan as a reverse proxy on the default port of `8000`. For example, with curl, you can use Meeshkan as a proxy like so.

```bash
$ curl http://localhost:8000/http://api.example.com
```

By default the recording proxy uses the first path items to navigate to a target host.
Now you should have the `logs` folder with jsonl files and the `__unmock__` folder with ready openapi schemes.

For more advanced information about recording, including custom middleware, see the [server documentation](./meeshkan/server/SERVER.md).

## Converting

Meeshkan provides utilities to convert from certain popular recording formats to the `.jsonl` format.

### Converting from pcap

You can convert [packet capture files](https://en.wikipedia.org/wiki/Pcap) to [HTTP Types](https://meeshkan.github.io/http-types/) format using the `convert` command:

```bash
meeshkan convert -i /path/to/file.pcap -o recordings.jsonl
```

**Executable [tshark](https://www.wireshark.org/docs/man-pages/tshark.html) must be present in your PATH.**

Converter does not decrypt captured packages, so only files containing plain unencrypted HTTP traffic are currently supported.

## Development

### Getting started

1. Create virtual environment
1. Install dependencies: `pip install --upgrade -e '.[dev]'`

### Tests

Run all checks:

```bash
$ python setup.py test
```

#### `pytest`

Run [tests/](https://github.com/Meeshkan/meeshkan/tree/master/tests/) with `pytest`:

```bash
pytest
# or
python setup.py test
```

Configuration for `pytest` is found in [pytest.ini](https://github.com/Meeshkan/meeshkan/tree/master/pytest.ini).

#### `black`

Run format checks:

```bash
$ black --check .
```

Fix formatting:

```bash
$ black .
```

#### `flake8`

Run style checks:

```bash
$ flake8 .
```

#### `pyright`

Run type-checking by installing [pyright](https://github.com/microsoft/pyright) globally and running

```bash
pyright --lib
# or
python setup.py typecheck
```

Using the [Pyright extension](https://marketplace.visualstudio.com/items?itemName=ms-pyright.pyright) is recommended for development in VS Code.

### Automated builds

Configuration for CircleCI [build pipeline](https://app.circleci.com/github/Meeshkan/meeshkan/pipelines) can be found in [.circleci/config.yml](https://github.com/Meeshkan/meeshkan/tree/master/.circleci/config.yml).

### Publishing package

1. Bump the version in [setup.py](https://github.com/Meeshkan/meeshkan/tree/master/setup.py) if the version is the same as in the published [package](https://pypi.org/project/meeshkan/). Commit and push.
1. Run `python setup.py test`, `python setup.py typecheck` and `python setup.py dist` to check everything works
1. To build and upload the package, run `python setup.py upload`. Insert PyPI credentials to upload the package to `PyPI`. The command will also run `git tag` to tag the commit as a release and push the tags to remote.

To see what the different commands do, see `Command` classes in [setup.py](https://github.com/Meeshkan/meeshkan/tree/master/setup.py).

## Contributing

Thanks for wanting to contribute! Take a look at our [development guide](#development) for notes on how to develop the package locally.

Please note that this project is governed by the [Meeshkan Community Code of Conduct](https://github.com/Meeshkan/code-of-conduct). By participating in this project, you agree to abide by its terms.
