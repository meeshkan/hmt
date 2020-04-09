# Mem

[![CircleCI](https://circleci.com/gh/mem/mem.svg?style=shield)](https://circleci.com/gh/mem/mem)
[![PyPI](https://img.shields.io/pypi/dm/mem.svg)](https://pypi.org/project/mem/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://black.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

Mem is a tool that mocks HTTP APIs for use in sandboxes as well as for automated and exploratory testing. It uses a combination of API definitions, recorded traffic and code in order to make crafting mocks as enjoyable as possible.

[Chat with us on Gitter](https://gitter.im/mem/community) to let us know about questions, problems or ideas!

## What's in this document

- [Installation](#installation)
- [Getting started with Mem](#getting-started-with-mem)
  - [Tutorial](#tutorial)
- [Collect recordings of API traffic](#collect-recordings-of-api-traffic)
- [Build a Mem spec from recordings](#build-a-mem-spec-from-recordings)
  - [Building modes](#building-modes)
- [Mock server traffic using a Mem spec](#mock-server-traffic-using-a-mem-spec)
- [Development](#development)
  - [Getting started](#getting-started)
  - [Tests](#tests)
  - [Type-checking](#type-checking)
  - [Automated builds](#automated-builds)
  - [Publishing Mem as a PyPi package](#publishing-mem-as-a-pypi-package)
- [Contributing](#contributing)
  - [Code of Conduct](#code-of-conduct)

## Installation
Install via [pip](https://pip.pypa.io/en/stable/installing/) (requires **Python 3.6+**):

```bash
pip install mem
```

macOS users can install Mem with [Homebrew](https://brew.sh/):

```sh
brew tap mem/tap
brew install mem
```

Debian and Ubuntu users can install Mem with `apt`:

```sh
echo "deb [trusted=yes] https://dl.bintray.com/mem/apt all main" | tee -a /etc/apt/sources.list
apt-get -qq update && apt-get install mem
```


## Getting started with Mem

The basic Mem flow is **collect, build and mock.**
1. First, **collect** data from recorded server traffic and/or OpenAPI specs.
1. Then, **build** a schema that unifies these various data sources.
1. Finally, use this schema to create a **mock** server of an API.

### Tutorial

The quickest way to get an overview of Mem is to complete our interactive tutorial. It walks you through the collect, build, and mock flow - while also covering the concepts necessary for development.

First, install `mem-tutorial` via [pip](https://pip.pypa.io/en/stable/installing/):

```bash
$ pip install mem-tutorial
$ mem-tutorial
```

_Note: This tutorial has been tested on Python 3.6, 3.7, and 3.8._

After installing, you can begin the tutorial by invoking from the command line:

```bash
$ mem-tutorial
```

Once you've run this, you should see:

```bash
                             __    __
   ____ ___  ___  ___  _____/ /_  / /______ _____
  / __ `__ \/ _ \/ _ \/ ___/ __ \/ //_/ __ `/ __ \
 / / / / / /  __/  __(__  ) / / / ,< / /_/ / / / /
/_/ /_/ /_/\___/\___/____/_/ /_/_/|_|\__,_/_/ /_/


The tutorial!!
Press ENTER to continue...
```

If not, it's probably our fault. Please let us know by [opening an issue](https://github.com/meeshkan/mem/issues).

## Collect recordings of API traffic

Let's look at how to build a Mem spec. First, you have to **collect** recordings of server traffic and/or OpenAPI server specs.

To record API traffic, the Mem CLI provides a `record` mode that captures API traffic using a proxy.

```bash
$ mem record
```

This command starts Mem as a reverse proxy on the default port of `8000` and creates two directories: `logs` and `specs`. 

With [curl](https://curl.haxx.se/), for example, you can use Mem as a proxy like so:

```bash
$ curl http://localhost:8000/http://api.example.com
```

By default, the recording proxy treats the path as the target URL. It then writes a [`.jsonl`](https://jsonlines.org) file containing logs of all server traffic to the `logs` directory.  All logs are created in the [`http-types`](https://github.com/meeshkan/http-types) format. This is because Mem's `build` tool expects all recordings to be represented in a `.jsonl` file containing recordings represented in the `http-types` format.

For more information about recording, including direct file writing and kafka streaming, see the [recording documentation](./docs/RECORD.md).

## Build a Mem spec from recordings

Using the Mem CLI, you can **build** an OpenAPI schema from a single `.jsonl` file, in addition to any existing OpenAPI specs that describe how your service works.

```bash
$ mem build --input-file path/to/recordings.jsonl 
```

_Note: The input file should be in [JSON Lines](http://jsonlines.org/) format and every line should be in [http-types](https://meeshkan.github.io/http-types/) JSON format. For an example input file, see [recordings.jsonl](./resources/recordings.jsonl)._

Optionally, you can also specify an output directory using the `--out` flag followed by the path to this directory. By default, Mem will build the new OpenAPI specifications in the `specs` directory. 

Use dash (`--input-file -`) to read from standard input:

```bash
$ mem build --input-file - < recordings.jsonl
```
### Building modes
You can use a mode flag to indicate how the OpenAPI spec should be built, for example:

```bash
mem build --input-file path/to/recordings.jsonl --mode gen
```

Supported modes are:
* gen [default] - infer a schema from the recorded data
* replay - replay the recorded data based on exact matching

For more information about building, including mixing together the two modes and editing the created OpenAPI schema, see the [building documentation](./docs/BUILD.md).

## Mock server traffic using a Mem spec

You can use an OpenAPI spec, such as the one created with `mem build`, to create a **mock** server using Mem.

```bash
$ mem mock path/to/dir/
```

_Note: You can specify a path to the directory your OpenAPI spec is in or a path to one specific file._

For more information about mocking, including adding custom middleware and modifying the mocking schema JIT via an admin API, see the [mocking documentation](./docs/MOCK.md).

## Development

Here are some useful tips for building and running Mem from source. 

If you run into any issues, please [reach out to our team on Gitter](https://gitter.im/meeshkan/community).

### Getting started

1. Clone this repository: `git clone https://github.com/meeshkan/mem`
1. Create a virtual environment: `virtualenv .venv && source .venv/bin/activate`
1. Install dependencies: `pip install --upgrade -e '.[dev]'`

### Tests

Run all checks:

```bash
$ python setup.py test
```

#### `pytest`

Run [tests/](https://github.com/meeshkan/mem/tree/master/tests/) with `pytest`:

```bash
pytest
# or
python setup.py test
```

Configuration for `pytest` is found in [pytest.ini](https://github.com/meeshkan/mem/tree/master/pytest.ini).

#### Formatting

Formatting is checked by the above mentioned `python setup.py test` command.

To fix formatting:

```sh
$ python setup.py format
```

#### `flake8`

Run style checks:

```bash
$ flake8 .
```

#### `pyright`

You can run type-checking by installing [pyright](https://github.com/microsoft/pyright) globally:

```bash
$ npm -i -g pyright
```

And then running:

```bash
$ pyright --lib
$ # or
$ python setup.py typecheck
```

Using the [Pyright extension](https://marketplace.visualstudio.com/items?itemName=ms-pyright.pyright) is recommended for development in VS Code.

### Automated builds

Configuration for CircleCI [build pipeline](https://app.circleci.com/github/meeshkan/mem/pipelines) can be found in [.circleci/config.yml](https://github.com/meeshkan/mem/tree/master/.circleci/config.yml).

### Publishing Mem as a PyPi package

To publish Mem as a PyPi package, complete the following steps:

1. Bump the version in [setup.py](https://github.com/meeshkan/mem/tree/master/setup.py) if the version is the same as in the published [package](https://pypi.org/project/mem/). Commit and push.
1. Run `python setup.py test` to check that everything works
1. To build and upload the package, run `python setup.py upload`. Insert PyPI credentials to upload the package to `PyPI`. The command will also run `git tag` to tag the commit as a release and push the tags to remote.

> To see what the different commands do, see `Command` classes in [setup.py](https://github.com/meeshkan/mem/tree/master/setup.py).

## Contributing

Thanks for your interest in contributing! Please take a look at our [development guide](#development) for notes on how to develop the package locally.  A great way to start contributing is to [file an issue](https://github.com/meeshkan/mem/issue) or [make a pull request](https://github.com/meeshkan/mem/pulls).

### Code of Conduct

Please note that this project is governed by the [Mem Community Code of Conduct](https://github.com/meeshkan/code-of-conduct). By participating, you agree to abide by its terms.
