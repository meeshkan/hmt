# Meeshkan

[![CircleCI](https://circleci.com/gh/Meeshkan/meeshkan.svg?style=svg)](https://circleci.com/gh/Meeshkan/meeshkan)
[![PyPI](https://img.shields.io/pypi/dm/meeshkan.svg)](https://pypi.org/project/meeshkan/)

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

You can convert [packet capture files](https://en.wikipedia.org/wiki/Pcap) to `http-types` recordings format using the `convert` command:

```bash
meeshkan convert -i /path/to/file.pcap -o recordings.jsonl
```

**Executable [tshark](https://www.wireshark.org/docs/man-pages/tshark.html) must be present in your PATH.**

Note that no decryption is made in the conversion so only packet capture files containing plain HTTP traffic are currently supported.

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

## Contributing

Thanks for wanting to contribute! Take a look at our [development guide](#development) for notes on how to develop the package locally.

Please note that this project is governed by the [Unmock Community Code of Conduct](https://github.com/unmock/code-of-conduct). By participating in this project, you agree to abide by its terms.
