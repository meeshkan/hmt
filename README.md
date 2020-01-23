# Meeshkan

[![CircleCI](https://circleci.com/gh/Meeshkan/meeshkan.svg?style=shield)](https://circleci.com/gh/Meeshkan/meeshkan)
[![PyPI](https://img.shields.io/pypi/dm/meeshkan.svg)](https://pypi.org/project/meeshkan/)
[![PyPi](https://img.shields.io/pypi/pyversions/meeshkan)](https://pypi.org/project/meeshkan/)
[![License](https://img.shields.io/pypi/l/meeshkan)](LICENSE)

Reverse engineer services with style 🤓💾🚀

## Table of Contents

1. [Installation](#installation)
1. [Command-line interface](#command-line-interface)
1. [Development](#development)
1. [Contributing](#contributing)

## Installation

Install via [pip](https://pip.pypa.io/en/stable/installing/):

```bash
$ pip install meeshkan
```

Note that `meeshkan` requires **Python 3.6+.**

## Command-line interface

To list available commands, execute `meeshkan` or `meeshkan --help`.

### Building OpenAPI from recordings

Build OpenAPI schema from recordings:

```bash
$ meeshkan build -i path/to/recordings.jsonl [-o path/to/output_directory]
```

The supported input format for recordings is in the [HTTP Types](https://github.com/Meeshkan/http-types) JSON format. The libraries listed there may be used to generate input files in your language of choice. For an example input file, see [recordings.jsonl](https://github.com/Meeshkan/meeshkan/blob/master/resources/recordings.jsonl).

Use dash (`-i -`) to read from standard input:

```bash
$ meeshkan build -i - < recordings.jsonl
```

### Converting from pcap

You can convert [packet capture files](https://en.wikipedia.org/wiki/Pcap) to [HTTP Types](https://github.com/Meeshkan/http-types) format using the `convert` command:

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

Run [tests/](./tests/) with `pytest`:

```bash
pytest
# or
python setup.py test
```

Configuration for `pytest` is found in [pytest.ini](./pytest.ini).

### Type-checking

Run type-checking by installing [pyright](https://github.com/microsoft/pyright) globally and running

```bash
pyright --lib
# or
python setup.py typecheck
```

Using the [Pyright extension](https://marketplace.visualstudio.com/items?itemName=ms-pyright.pyright) is recommended for development in VS Code.

### Automated builds

Configuration for CircleCI [build pipeline](https://app.circleci.com/github/Meeshkan/meeshkan/pipelines) can be found in [.circleci/config.yml](./.circleci/config.yml).

### Publishing package

1. Bump the version in [setup.py](./setup.py) if the version is the same as in the published [package](https://pypi.org/project/meeshkan/). Commit and push.
1. Run `python setup.py test`, `python setup.py typecheck` and `python setup.py dist` to check everything works
1. To build and upload the package, run `python setup.py upload`. Insert PyPI credentials to upload the pacakge to `PyPI`. The command will also run `git tag` to tag the commit as a release and push the tags to remote.

To see what the different commands do, see `Command` classes in [setup.py](./setup.py).

## Contributing

Thanks for wanting to contribute! Take a look at our [development guide](#development) for notes on how to develop the package locally.

Please note that this project is governed by the [Meeshkan Community Code of Conduct](https://github.com/Meeshkan/code-of-conduct). By participating in this project, you agree to abide by its terms.
