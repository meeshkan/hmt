# Meeshkan

[![CircleCI](https://circleci.com/gh/meeshkan/meeshkan.svg?style=shield)](https://circleci.com/gh/meeshkan/meeshkan)
[![PyPI](https://img.shields.io/pypi/dm/meeshkan.svg)](https://pypi.org/project/meeshkan/)
[![PyPi](https://img.shields.io/pypi/pyversions/meeshkan)](https://pypi.org/project/meeshkan/)
[![License](https://img.shields.io/pypi/l/meeshkan)](LICENSE)

Meeshkan is a tool that mocks HTTP APIs for use in sandboxes as well as for automated and exploratory testing. It uses a combination of API definitions, recorded traffic and code in order to make crafting mocks as enjoyable as possible.


## What's in this document

- [Installation](#installation)
- [Getting started with Meeshkan](#getting-started-with-meeshkan)
- [Collect recordings of API traffic](#collect-recordings-of-api-traffic)
- [Build a Meeshkan spec from recordings](#build-a-meeshkan-spec-from-recordings)
- [Mock server traffic using a Meeshkan spec](#mock-server-traffic-using-a-meeshkan-spec)
- [Development](#development)
- [Contributing](#contributing)

## Installation

Install via [pip](https://pip.pypa.io/en/stable/installing/):

```bash
$ pip install meeshkan
```

Note that `meeshkan` requires **Python 3.6+.**

## Getting started with Meeshkan

The basic Meeshkan flow is **collect, build and mock.**
1. To start, **collect** data from recorded server traffic and/or OpenAPI specs.
1. Then, **build** a schema that unifies these various data sources.
1. Finally, use this schema to create a **mock** server of an API.

### Tutorial

The quickest way to get an overview of Meeshkan is to complete our [interactive tutorial](https://github.com/meeshkan/meeshkan-tutorial). It walks you through the collect, build, and mock flow - while also covering the concepts necessary for development.

### Hello world

```bash
$ meeshkan record -r --daemon # start the recorder in daemon mode
$ curl http://localhost:8000 -H '{"Host": "time.jsontest.com" }' # record traffic
$ meeshkan record --stop-daemon # stop the daemon
$ meeshkan build
$ meeshkan mock -r --daemon # start the mocking server in daemon mode
$ curl http://localhost:8000 -H '{"Host": "time.jsontest.com" }' # mock traffic
$ meeshkan mock --stop-daemon # stop the daemon
```

## Collect recordings of API traffic

Let's look at how to build a Meeshkan spec. First, you have to **collect** recordings of server traffic and/or OpenAPI server specs.

To record API traffic, the Meeshkan CLI provides a `record` mode that captures API traffic using a proxy.

```bash
$ pip install meeshkan # if not installed yet
$ meeshkan record
```

This starts Meeshkan as a reverse proxy on the default port of `8000`.  For example, with curl, you can use Meeshkan as a proxy like so:

```bash
$ curl http://localhost:8000/http://api.example.com
```

By default, the recording proxy treats the path as the target URL and writes a [`.jsonl`](https://jsonlines.org) file containing logs of all server traffic to a `logs` directory.  All logs are created in the [`http-types`](https://github.com/meeshkan/http-types) format.  The `meeshkan build` tool expects all recordings to be represented in a `.jsonl` file containing recordings represented in the `http-types` format.

For more information about recording, including direct file writing and kafka streaming, see the [recording documentation](./guides/RECORD.md).

## Build a Meeshkan spec from recordings

Using the Meeshkan CLI, you can **build** an OpenAPI schema from a single `.jsonl` file, in addition to any existing OpenAPI specs that describe how a service works.

```bash
$ pip install meeshkan # if not done yet
$ meeshkan build -i path/to/recordings.jsonl [-o path/to/output_directory]
```

The input file should be in [JSON Lines](http://jsonlines.org/) format and every line should be in [HTTP Types](https://meeshkan.github.io/http-types/) JSON format. 

For an example input file, see [recordings.jsonl](https://github.com/Meeshkan/meeshkan/blob/master/resources/recordings.jsonl). The libraries listed at [HTTP Types](https://meeshkan.github.io/http-types/) can be used to generate input files in your language of choice.

Use dash (`-i -`) to read from standard input:

```bash
$ meeshkan build --source file -i - < recordings.jsonl
```
### Building modes
You can use a mode flag to indicate how the OpenAPI spec should be built, ie:

```bash
meeshkan build -i path/to/recordings.jsonl --mode gen
```

Supported modes are:
* gen [default] - infer a schema from the recorded data
* replay - replay the recorded data based on exact matching

For more information about building, including mixing together the two modes and editing the created OpenAPI schema, see the [building documentation](./guides/BUILD.md).

## Mock server traffic using a Meeshkan spec

You can use an OpenAPI spec, such as the one created with `meeshkan build` to create a **mock** server using Meeshkan.

```bash
$ pip install meeshkan # if not installed yet
$ meeshkan mock
```

For more information about mocking, including adding custom middleware and modifying the mocking schema JIT via an admin API, see the [mocking documentation](./guides/MOCK.md).

## Development

Here are some useful tips for building and running Meeshkan from source.

### Getting started

1. Create a virtual environment: `virtualenv .venv && source .venv/bin/activate`
1. Install dependencies: `pip install --upgrade -e '.[dev]'`

### Tests

You can run the  [tests/](https://github.com/Meeshkan/meeshkan/tree/master/tests/) with `pytest`:

```bash
pytest
# or
python setup.py test
```

Configuration for `pytest` is found in [pytest.ini](https://github.com/Meeshkan/meeshkan/tree/master/pytest.ini).

### Type-checking

You can run type-checking by installing [pyright](https://github.com/microsoft/pyright) globally and running:

```bash
pyright --lib
# or
python setup.py typecheck
```

Using the [Pyright extension](https://marketplace.visualstudio.com/items?itemName=ms-pyright.pyright) is recommended for development in VS Code.

### Automated builds

Configuration for CircleCI [build pipeline](https://app.circleci.com/github/Meeshkan/meeshkan/pipelines) can be found in [.circleci/config.yml](https://github.com/Meeshkan/meeshkan/tree/master/.circleci/config.yml).

### Publishing Meeshkan as a PyPi package

To publish Meeshkan as a PyPi package, please do the following steps:

1. Bump the version in [setup.py](https://github.com/Meeshkan/meeshkan/tree/master/setup.py) if the version is the same as in the published [package](https://pypi.org/project/meeshkan/). Commit and push.
1. Run `python setup.py test`, `python setup.py typecheck` and `python setup.py dist` to check everything works
1. To build and upload the package, run `python setup.py upload`. Insert PyPI credentials to upload the package to `PyPI`. The command will also run `git tag` to tag the commit as a release and push the tags to remote.

To see what the different commands do, see `Command` classes in [setup.py](https://github.com/Meeshkan/meeshkan/tree/master/setup.py).

## Contributing

Thanks for your interest in contributing! Please take a look at our [development guide](#development) for notes on how to develop the package locally.  A great way to start contributing is to [file an issue](https://github.com/meeshkan/meeshkan/issue) or [make a pull request](https://github.com/meeshkan/meeshkan/pulls).

Please note that this project is governed by the [Meeshkan Community Code of Conduct](https://github.com/Meeshkan/code-of-conduct). By participating, you agree to abide by its terms.
