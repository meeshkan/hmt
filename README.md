# Meeshkan

[![CircleCI](https://circleci.com/gh/Meeshkan/meeshkan.svg?style=shield)](https://circleci.com/gh/Meeshkan/meeshkan)
[![PyPI](https://img.shields.io/pypi/dm/meeshkan.svg)](https://pypi.org/project/meeshkan/)
[![PyPi](https://img.shields.io/pypi/pyversions/meeshkan)](https://pypi.org/project/meeshkan/)
[![License](https://img.shields.io/pypi/l/meeshkan)](LICENSE)

Meeshkan is a library and command-line tool for reverse engineering APIs from recorded traffic.

It is used at [Meeshkan](https://meeshkan.com) to build enterprise-level API sandboxes.

The supported input format for HTTP recordings is the [HTTP Types](https://github.com/Meeshkan/http-types) JSON format.

Meeshkan requires Python 3.6 or later for the new async/await syntax.

Meeshkan is statically typed using the [pyright](https://github.com/microsoft/pyright) type checker.

## Table of Contents

1. [Installation](#installation)
1. [Python API](#python-api)
1. [Command-line interface](#command-line-interface)
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
from openapi_typed import OpenAPIObject
import meeshkan
from typing import List
import json
from http_types import HttpExchange, Request, Response, RequestBuilder


def read_http_exchanges() -> List[HttpExchange]:
    """Read HTTP exchanges from the source of your choice.
    """
    request: Request = RequestBuilder.from_url(
        "https://example.org/v1", method="get", headers={})

    response: Response = Response(
        statusCode=200, body=json.dumps({"hello": "world"}), headers={})

    http_exchange: HttpExchange = {'request': request, 'response': response}

    return [http_exchange]


http_exchanges = read_http_exchanges()

# Build OpenAPI schema from a list of recordings
openapi: OpenAPIObject = meeshkan.build_schema_batch(http_exchanges)

# Build schema from an iterator
openapi: OpenAPIObject = meeshkan.build_schema_online(iter(http_exchanges))

# Update OpenAPI schema one `HttpExchange` at a time
http_exchange = http_exchanges[0]
openapi: OpenAPIObject = meeshkan.update_openapi(openapi, http_exchange)
```

## Command-line interface

To list available commands, execute `meeshkan` or `meeshkan --help`.

### Create OpenAPI schema from HTTP recordings

Build OpenAPI schema from a single `recordings.jsonl` file:

```bash
$ meeshkan build --source file -i path/to/recordings.jsonl [-o path/to/output_directory]
```

The input file should be in [JSON Lines](http://jsonlines.org/) format and every line should be in [HTTP Types](https://meeshkan.github.io/http-types/) JSON format.For an example input file, see [recordings.jsonl](https://github.com/Meeshkan/meeshkan/blob/master/resources/recordings.jsonl). The libraries listed at [HTTP Types](https://meeshkan.github.io/http-types/) can be used to generate input files in your language of choice.

Use dash (`-i -`) to read from standard input:

```bash
$ meeshkan build --source file -i - < recordings.jsonl
```

#### Reading from Kafka

Install `kafka` bundle: `pip install meeshkan[kafka]` and set `--source kafka`:

```bash
$ meeshkan build --source kafka [-o path/to/output_directory]
```

_TODO: Configuration for Kafka_

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

Run [tests/](https://github.com/Meeshkan/meeshkan/tree/master/tests/) with `pytest`:

```bash
pytest
# or
python setup.py test
```

Configuration for `pytest` is found in [pytest.ini](https://github.com/Meeshkan/meeshkan/tree/master/pytest.ini).

### Type-checking

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
