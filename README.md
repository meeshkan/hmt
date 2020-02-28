# Meeshkan

[![CircleCI](https://circleci.com/gh/meeshkan/meeshkan.svg?style=shield)](https://circleci.com/gh/meeshkan/meeshkan)
[![PyPI](https://img.shields.io/pypi/dm/meeshkan.svg)](https://pypi.org/project/meeshkan/)
[![PyPi](https://img.shields.io/pypi/pyversions/meeshkan)](https://pypi.org/project/meeshkan/)
[![License](https://img.shields.io/pypi/l/meeshkan)](LICENSE)

Meeshkan is a tool that mocks HTTP APIs for use in sandboxes as well as for automated and exploratory testing. It uses a combination of API definitions, recorded traffic and code in order to make crafting mocks as enjoyable as possible.

Meeshkan requires Python 3.6 or later.

## Table of Contents

1. [Installation](#installation)
1. [Hello world](#hello-world)
1. [Collect](#collect)
1. [Build](#build)
1. [Mock](#mock)
1. [Development](#development)
1. [Contributing](#contributing)

## Installation

Install via [pip](https://pip.pypa.io/en/stable/installing/):

```bash
$ pip install meeshkan
```

Note that `meeshkan` requires **Python 3.6+.**

## Hello world

The basic Meeshkan flow is **collect, build and mock.**
1. Start by **collecting** data from recorded server traffic and OpenAPI specs.
1. Then, **build** a schema that unifies these various data sources.
1. Finally, use this schema to create a **mock** server of an API.

```bash
$ meeshkan record -r --daemon # start the recorder in daemon mode
$ curl http://localhost:8000 -H '{"Host": "time.jsontest.com" }' # record traffic
$ meeshkan record --stop-daemon # stop the daemon
$ meeshkan build
$ meeshkan mock -r --daemon # start the mocking server in daemon mode
$ curl http://localhost:8000 -H '{"Host": "time.jsontest.com" }' # mock traffic
$ meeshkan mock --stop-daemon # stop the daemon
```

## Record

Meeshkan provides a recorder that can capture API traffic using a proxy.

```bash
$ pip install meeshkan # if not installed yet
$ meeshkan record
```

This starts Meeshkan as a reverse proxy on the default port of `8000`.  For example, with curl, you can use Meeshkan as a proxy like so.

```bash
$ curl http://localhost:8000/http://api.example.com
```
By default the recording proxy treats the path as the target URL.

Now you should have the `logs` folder with jsonl files and the `__unmock__` folder with ready openapi schemes. 

For more advanced information about recording, including custom middleware, see the [server documentation](./meeshkan/server/SERVER.md).

## Build

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
* gen [default] - infer a schema from the recorded data
* replay - replay the recorded data based on exact matching
* mixed - replay the recorded data based on exact matching when it is possible

The OpenAPI schemas can be manually edited to mix the two modes.

## Mock

You can use an existing OpenAPI spec, an OpenAPI spec you've built using `meeshkan build`, and recordings to create a mock server using Meeshkan.

```bash
$ pip install meeshkan # if not installed yet
$ meeshkan mock
```

### Common command-line arguments

The following commands are available in mock mode:

| Argument     | Description | Default |
| ------------ | ----------- | ------- |
| `port`       | Server port | 8000    |
| `admin_port` | Admin port  | 8999    |
| `log_dir`    | The directory containing `.jsonl` files for mocking directly from recorded fixtures | `logs` |
| `specs_dir`  | The directory containing `.yml` or `.yaml` OpenAPI specs used for mocking, including ones built using `meeshkan build` | `specs` |

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
