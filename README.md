# Meeshkan

[![CircleCI](https://circleci.com/gh/Meeshkan/meeshkan.svg?style=svg)](https://circleci.com/gh/Meeshkan/meeshkan)

Reverse engineer services with style 🤓💾🚀

**Requires Python 3.6+**.

## Usage

**Documentation coming soon.**

## Development

### Getting started

1. Create virtual environment
1. Install dependencies: `pip install --upgrade -e .[dev]`

### Invoking CLI

See all commands:

```
$ meeshkan --help
```

#### Building schemas

Build OpenAPI schema from recordings:

```bash
$ meeshkan build -i resources/sample.jsonl [-o path/to/output.yaml]
```

Use `-i -` to read from standard input.

See help for `build` command:

```bash
$ meeshkan build --help
```

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
