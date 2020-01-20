# Meeshkan

Reverse engineer services with style 🤓💾🚀

Full documentation coming soon.

**Requires Python 3.6+**.

## Development

### Getting started

1. Create virtual environment
1. Install dependencies: `pip install --upgrade -e .[dev]`

**Requires Python 3.6+**.

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
