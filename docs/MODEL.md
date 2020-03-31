# Definitive guide to testing APIs with Meeshkan

Every API mocked by Meeshkan is an instance of `Model` powered by [Hypothesis strategies](https://hypothesis.readthedocs.io/en/latest/data.html). Hypothesis strategies are made for generating arbitrary data in a controlled manner. Meeshkan models are designed for testing properties of your system instead of hard-coded examples, a premise of property-based testing (PBT). While PBT is a first-class citizen in Meeshkan, you can still use it also for regular unit testing.

Below, we go through examples of how models and data generators can help mocking external services in different use cases. We'll first cover the simpler _non-stateful_ case where your tests do not depend on the internal state of the model (think of first creating a user and then querying the user, ending with deleting the user). After covering stateless testing, we'll look into using Meeshkan's Model API to maintain internal state in model's for testing _stateful_ behaviour. This is where property-based testing starts to shine, as you can cover complex flows you could have never imagined (but rest assured, your users would eventually discover them).

## API client testing (stateless)

Assume you're building a service depending on an external service. The service could be your company's internal microservice or a third-party API such as [OP Bank](https://op-developer.fi/docs). Because you cannot test your application against the production API, you need to mock the API in your tests.

> If you're lucky, your service has a _sandbox_ that you can use for testing. For example, OP Bank has a [sandbox](https://op-developer.fi/docs#user-content-2-test-apis-in-sandbox) that's very useful for prototyping your application. However, andboxes typically have limitations not only on the number of calls you can make but also in their behaviour. For example, the OP Bank sandbox always returns the same data for the same call, so you cannot test tricky cases such as the server failing with an internal server error or customer having no accounts.

The following steps depend on whether you have an OpenAPI document available or not. If your external service provides an OpenAPI document documenting the API's behaviour, you can create a Meeshkan model with `Model.from_openapi` method:

```python
from meeshkan import Model

opbank = Model.from_openapi("op-bank.openapi.json")
```

If your service provider doesn't provide an OpenAPI specification, you need to create a specification yourself. Luckily, it's not that hard. You only need to create an instance `OpenAPIObject` as follows:

```python
from openapi_typed_2 import OpenAPIObject

openapi = OpenAPIObject(...)
```

When you're done, you create a model from `OpenAPIObject` with `Model.from_openapi`:

```python
from meeshkan import Model

model = Model.from_openapi(openapi)
```

### Generating responses

Once you have a model, you can use it to generate _responses from requests_, everything you need to thoroughly test your API client code. To generate responses, you first invoke the `mock` method in `Model`:

```python
mock = model.mock()
```

Here, `mock` has a `strategy_from` method that, when called with an `HttpRequest` object, creates a `SearchStrategy` object. You rarely need to call it yourself, but to understand how Meeshkan works, let us see it in action:

```python
from http_typed import Request, RequestBuilder
request = RequestBuilder.from_url("https://api.opbank.com/v4/accounts")  # typeof: Request

responses = mock.strategy_from(request)  # typeof: hypothesis.SearchStrategy
```

Now we can request example responses from the generator:

```python
>>> responses.example()
<Response(status_code=200, body={ accounts: [] }, headers={})>

>>> responses.example()
<Response(status_code=500, body="Internal Server Error", headers={})>
```

As you can see, `responses.example()` generates responses randomly. What if I want to test a case where the server returns 500? You transform the `mock` with `filter`:

```python
>>> filtered = responses.filter(lambda r: r.status_code == 500)
>>> filtered.example()
<Response(status_code=500, body="Internal Server Error", headers={})>
>>> filtered.example()
<<Response(status_code=500, body="Internal Server Error", headers={})>
```

You can similarly use `.map()` to fix response body:

```python
>>> mapped = responses.map(lambda r: r.replace(body={ "Hello": "World"}))
>>> mapped.example()
<Response(status_code=200, body={ "Hello": "World" }, headers={})>
```

In practice, you don't create strategies yourself but you apply `map`, `filter`, etc. on `mock` objects directly:

```python
mock = model.mock()
mock = mock.map(lambda r: r.replace(body={ "Hello": "World}))
mock = mock.filter(lambda r: r.status_code == 200)
```

When `mock` then creates a `SearchStrategy` from a `Request` object, all of the transformations applied to `mock` will be applied to the `SearchStrategy` object.

### Restricting mockers

When transforming mockers, you may not want to transform responses from all paths but only from specific ones. The solution is to create multiple mockers that accept different paths. `model.mock` accepts a predicate of type `Callable[[Request], bool]`. The predicate defines which requests the mocker should accept as valid requests.

For example, you can create a mocker that only handles calls to paths starting with `/personal/v4`:

```python
mocker = model.mock(lambda req: req.path.starts_with("/personal/v4"))
```

If you then try to generate a search strategy from a request with different path, you will get an exception:

```python
>>> mocker.strategy_from(RequestBuilder.from_url("https://example.com/personal/v3))
<MockerException>
```

### Using `mocker` for intercepting requests

How to use `mocker` objects for testing our code? When your code performs a network call, the call needs to be intercepted so a mock can be served in response. Meeshkan provides `intercept_with` method that accepts an instance of `Mocker`. Here's a full example:

```python
opbank = Model.from_openapi("opbank.openapi.json")

def test_opbank_returns_500():
    # Add maps and filters to control generated data
    # Type of mocker is `Callable[[Request], Generator[Response]]`
    # but it has `map`, `filter`, etc.
    mocker = opbank
        .mock(lambda req: r"/personal/v4/".test(req.path))
        .filter(lambda res: res.status_code == 500)

    # Intercept HTTP traffic and generate responses
    # with mocker
    with meeshkan.intercept_with(mocker):
        with pytest.raises(PaymentException):
            my_client.confirm_payment(payment)

def test_opbank_returns_200():
    mocker = opbank.mock(path="/personal/v4/*").filter(lambda res: res.status_code == 200)
    with meeshkan.intercept_with(response_gen)
        payment_result = my_client.confirm_payment(payment)

    assert payment_result.status == PAYMENTS.OK
```

Alternatively, you can use the interceptor as a decorator:

```python
mocker = opbank.mock().filter(lambda res: res.status_code == 200)

@meeshkan.intercept_with(mocker)
def test_opbank_returns_200():
    payment_result = my_client.confirm_payment(payment)
    assert payment_result.status == PAYMENTS.OK
    assert mocker.called_once
```

### Property-based testing

The examples above only ran the test once.

**TODO**

### Dockerized

To run a Meeshkan `Model` in Docker, you can use a following `Dockerfile`:

```Dockerfile
FROM python-3.8.0

RUN pip install meeshkan

# File containing a class inheriting `BaseModel`
ADD models.py

EXPOSE 8000

# Specify path to class in CMD
CMD ["meeshkan", "mock", "models:OpBank"]
```

This will start a Meeshkan mock server at port 8000.

TODO: How to interact with generators?

## API server testing (stateless)

Instances of `Model` can be used to generate requests that the API is expected to handle. The following illustrates the basic flow:

```python
from meeshkan.loaders import load_openapi
from meeshkan.models import Model

openapi = load_openapi("openapi.yaml")
model = Model.from_openapi(openapi)

# Generator of HttpRequest objects.
request_gen = model.requests()

# Generate example request
req = request_gen.example()

# Send request to locally running server
res = req.send("http://localhost:8000")

# Validate response against the request. For example, check that status code is one of those listed as valid responses for the given request.
model.validate(req, res)
```

To run property-based tests, you use `given` from Hypothesis library to generate test cases. For example:

```python
# Run 100 tests with different values for request and response context
@given(req=model.requests())
def test_everything(req):
    res = req.send("http://localhost:8000")
    assert model.validate(res)
```

To test specific cases, you can use all the tricks provided by [Hypothesis strategies](https://hypothesis.readthedocs.io/en/latest/data.html#adapting-strategies) to only generate requests you want to test. For example, you can use `map()`, `filter()`, `flatmap()`, and [`assume`](https://hypothesis.readthedocs.io/en/latest/details.html#hypothesis.assume).

```python
def add_auth(req):
    req.headers.Authorization = `"Bearer XYZ"
    return req

request_gen = model.request()
    .map(add_auth)
    .filter(matches_path(r"^\/v1\/accounts/"))

@given(req=request_gen)
def test_always_returns_valid(req):
    res = req.send("http://localhost:8000")
    assert model.validate(res)
    assert res.status_code == 200
```

## Stateful testing

**_Everything below is experimental_**

All the examples above were for testing **stateless** APIs, where every request is independent. This is sufficient for most use cases, but sometimes you need stateful behaviour.

### API client testing

**Requirements**

- _State-dependent draw_ strategies
- _Customizable `next_state(state, operation)`_

### API server testing

**Requirements**

- Model that can _drive stateful testing_
- _Commands, preconditions, next_state_
- Postconditions

_Important: Does not require stateful drawing!_

```python

class StateMachine(BaseStatefulModel, SearchStrategy):
    """Unlike state machines in stateful PBT that only
    need to cover `next_state` and `precondition`, this
    also needs to cover "drawing" to act in mocking.

    Arguments:
        BaseStatefulModel {[type]} -- [description]
        SearchStrategy {[type]} -- [description]
    """
    def __init__(self):
        super().__init__()
        self._state = {}

    def next_state(self, request, response):
        # Define all state transitions here
        ...

    def precondition(self, request) -> bool:
        # Define preconditions for an operation

    def postcondition(self, request, response) -> bool:
        # Define postconditions here
```

```python

model = Mode.fromOpenAPI()

state_machine = StateMachine()
model.attach(state_machine)

for cmds in commands():
    # Prepare empty state here
    prepare()

    results, state, history = model.run(cmds)


```

### Custom models

### Storage
