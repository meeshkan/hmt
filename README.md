# Meeshkan

[![CircleCI](https://circleci.com/gh/meeshkan/meeshkan.svg?style=shield)](https://circleci.com/gh/meeshkan/meeshkan)
[![PyPI](https://img.shields.io/pypi/dm/meeshkan.svg)](https://pypi.org/project/meeshkan/)
[![PyPi](https://img.shields.io/pypi/pyversions/meeshkan)](https://pypi.org/project/meeshkan/)
[![License](https://img.shields.io/pypi/l/meeshkan)](LICENSE)

Meeshkan helps developers write effective integration tests.

## When should you use integration tests?

If your app or service integrates with another app or service, integration testing is a good way to make sure that your app correctly handles input from that service, including unexpected input.

## Some nice articles on integration testing

- [Martin Fowler on integration testing](https://martinfowler.com/bliki/IntegrationTest.html)
- [Geeks for Geeks](https://www.geeksforgeeks.org/software-engineering-integration-testing/)
- [Unit testing vs integration testing](https://performancelabus.com/unit-vs-integration-testing/)

## How it works

Meeshkan starts from the premise that integrations are always two-sided:
- on one side, there is your app or service.
- on the other side, there is an app or service with which you're interacting.

These interactions are brokered through an API.  There are many different types of APIs (REST, gRPC, Kafka, GraphQL, SQL) but the basic idea is the same - you send a request and you get a response.

Meeshkan works by building a stand-in, or *mock*, of the service with which you integrate.  It does this by using various sources of information, like API recordings and OpenAPI specs, to reverse engineering a mock whose behavior is *close enough to* that of the original service. *Close enough* means, amongst other things:

- the data it serves back looks more or less like data from the real service.
- the mock fails when it should fail and succeeds when it should succeed.
- the mock can throw arbitrary errors or be sluggish.
- the mock can handle sequences of interactions correctly.

Then, when you test code that calls the service via an API, it will call this mock on a local server instead of calling the real servie. If you are an API provider, you can even use Meeshkan to maintain a sandbox version of your API that developers can use for integration testing.

## Installation
Install via [pip](https://pip.pypa.io/en/stable/installing/) (requires **Python 3.6+**):

```bash
$ pip install meeshkan
```

macOS users can install Meeshkan with [Homebrew](https://brew.sh/):

```sh
$ brew tap meeshkan/tap
$ brew install meeshkan
```

Debian and Ubuntu users can install Meeshkan with `apt-get`:
- echo "deb [trusted=yes] https://dl.bintray.com/meeshkan/apt all main" | tee -a /etc/apt/sources.list
- apt-get update -qq && apt-get install -y meeshkan


## Write your first integration test using Meeshkan

This guide uses python as an example language, but we have examples for several other languages as well:

- [JavaScript]()
- [Java]()
- [Go]()

In the example, we'll use a code that integrates with Stripe.  Why Stripe?  Why not!  But Meeshkan can be used for any REST API integration, and we're working hard to build gRPC, GraphQL, and Kafka too.

First, here's our integration code:

```python
# charge.py
import stripe
stripe.api_key = "wouldnt_you_like)to_know"

def charge_for_expensive_services(source):
  res = stripe.Charge.create(
    amount=1999,
    currency="usd",
    source=source,
    description="A charge for our most expensive service.",
  )
  return res.id
```

And here's our test:

```python
# charge_test.py
import meeshkan_client as meeshkan
import pytest
from meeshkan.behaviors import with_codes
from .charge import charge_for_expensive_services

meeshkan.on()
meeshkan.use('stripe')

def test_charge_200():
  meeshkan.transform(with_codes(200))
  id = charge_for_expensive_services('my_source')
  assert isinstance(id, str)

def test_charge_400():
  meeshkan.transform(with_codes(400))
  with pytest.raises(Exception) as e_info:
    charge_for_expensive_services('my_source')

def test_charge_500():
  meeshkan.transform(with_codes(500))
  with pytest.raises(Exception) as e_info:
    charge_for_expensive_services('my_source')
```

When we run `pytest`, we see the following:

```bash
pytest charge_test.py
############# something here ##############
```

In the console log above, we see several nifty features of Meeshkan:

1. The tests pass!  Meeshkan has fetched a mini version of stripe and used it for our integration test.
1. We use Meeshkan to control how the API behaves. For example, we tell it to succeed for one test and fail for two others.
1. The console gives us information about API coverage, meaning the additional tests we would need to write to have tested the most common outcomes. Here, we are missing the test for a `no_network` outcome, and Meeshkan lets us know. In fact, let's go back and write that test now!

```python
# charge_test.py
import meeshkan_client as meeshkan
import pytest
from meeshkan.behaviors import with_codes
from .charge import charge_for_expensive_services

meeshkan.on()
meeshkan.use('stripe')

def test_charge_200():
  meeshkan.transform(with_codes(200))
  id = charge_for_expensive_services('my_source')
  assert isinstance(id, str)

def test_failure():
  for failure_case in [with_codes(400), with_codes(500), no_network()]:
    meeshkan.transform(failure_case)
    with pytest.raises(Exception) as e_info:
      charge_for_expensive_services('my_source')
```

Behind the scenes, Meeshkan spins up a tiny (smöl) mock server that is responsible for acting like Stripe would.  You can start this server from the command line like so:

```bash
meeshkan mock --spec-dir path/to/specs
```

More on the CLI usage can be found in the [mocking documentatino](./MOCK.md).

## Making your own mock servers

The easiest way to use Meeshkan is to obtain a pre-existing mock like we do in the example above. However, in most cases, you will need to build your own. To make your own mock servers, you can currently import two types of information:

1. Recordings of server traffic in the [`http-types`](https://github.com/http-tyes) format, stored in a `.jsonl` file.
1. OpenAPI specs describing the server's behavior.

You can work with just one of these sources or both in conjunction.

Assuming that your `.jsonl` files are in a directory called `recordings` and your OpenAPI specs are in a directory called `specs`, you can build a Meeshkan mock using the following command:

```bash
meeshkan build --recordings-dir recordings/ --specs-dir specs/ --out-dir out/
```

If you'd like to test this out, you can use [this sample recording.jsonl file]() of the Stripe API in your `recordings/` directory and [this sample OpenAPI spec]() of the Stripe API in your `specs/` directory.

Now, `out/` will contain all of the information Meeshkan needs to create a mock of your service.  This spec can now be used in your test!  Revisiting the python example above, and assuming that it is run from the same directory containing `./out`, we can use this in our test:

```python
# charge_test.py
import meeshkan_client as meeshkan
import pytest
from meeshkan.behaviors import with_codes
from .charge import charge_for_expensive_services

meeshkan.on()
meeshkan.use('./out')

def test_charge_200():
  meeshkan.transform(with_codes(200))
  id = charge_for_expensive_services('my_source')
  assert isinstance(id, str)

def test_failure():
  for failure_case in [with_codes(400), with_codes(500), no_network()]:
    meeshkan.transform(failure_case)
    with pytest.raises(Exception) as e_info:
      charge_for_expensive_services('my_source')
```

Or, we can spin up a meeshkan mock server from the command line:

```bash
cd ./out && meeshkan mock
```

Meeshkan also offers an interactive builder mode where you can add or modify your mock's and explore how it works.  You can invoke this by using the --interactive flag, which will open the builder in a browser.

```bash
meeshkan build --interactive --recordings-dir recordings/ --specs-dir specs/ --out-dir out/
```

### Building modes
You can use a mode flag to indicate how the spec for the mock server should be built, for example:

```bash
meeshkan build -i path/to/recordings.jsonl --mode gen
```

Supported modes are:
* gen [default] - infer a schema from the recorded data
* replay - replay the recorded data based on exact matching

For more information about building, including mixing together the two modes and editing the created OpenAPI schema, see the [building documentation](./docs/BUILD.md).

## Collect recordings of API traffic

To record API traffic that can be onsumed by Meeshkan, the Meeshkan CLI provides a `record` mode that captures API traffic using a proxy.

```bash
$ pip install meeshkan # if not installed yet
$ meeshkan record
```

This starts Meeshkan as a reverse proxy on the default port of `8000`.  For example, with curl, you can use Meeshkan as a proxy like so:

```bash
$ curl http://localhost:8000/http://api.example.com
```

By default, the recording proxy treats the path as the target URL and writes a [`.jsonl`](https://jsonlines.org) file containing logs of all server traffic to a `logs` directory.  All logs are created in the [`http-types`](https://github.com/meeshkan/http-types) format.  The `meeshkan build` tool expects all recordings to be represented in a `.jsonl` file containing recordings represented in the `http-types` format.

The following libraries also exist to record HTTP traffic in the `http-types` format and/or stream it to a sink:

- [express-middleware]()
- [python-middleware]()
- [kafka-middleware]()
- [kong-plugin]()
- [datadog-plugin]()
- [apigee-plugin]()

For more information about recording, including direct file writing and kafka streaming, see the [recording documentation](./docs/RECORD.md).

## Community

[Chat with us on Gitter](https://gitter.im/meeshkan/community) to let us know about questions, problems or ideas!


## Some alternatives and competitors

- using a real API for integration testing
- using a fixture-serving library like
  - unmock
  - nock
  - HTTPretty
- pact.io
- hoverfly
- prism
- wiremock

## Development

Here are some useful tips for building and running Meeshkan from source. 

### Getting started

1. Clone this repository: `git clone https://github.com/meeshkan/meeshkan`
1. Create a virtual environment: `virtualenv .venv && source .venv/bin/activate`
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
