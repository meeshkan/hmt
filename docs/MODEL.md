# Meeshkan model

Every API mocked by Meeshkan is an instance of `Model`. `Model` is a **data generator**. Under the Hood, `Model` class is powered by [Hypothesis strategies](https://hypothesis.readthedocs.io/en/latest/data.html) generally used for property-based testing (PBT). In Meeshkan, PBT is a first-class citizen. 

Below, we go through examples of how models and data generators can help testing in most use cases.

## API client testing

### Python

```python
from models import opbank

def test_opbank_returns_500():
    # Add maps and filters to control generated data
    # Type of mocker is `Callable[[Request], Generator[Response]]`
    # but it has `map`, `filter`, etc.
    mocker = opbank.mock(path="/personal/v4/*").filter(status(500))
    with meeshkan.intercept_with(mocker):  # Intercept HTTP traffic when used as a context manager
        with pytest.raises(PaymentException):
            my_client.confirm_payment(payment)

def test_opbank_returns_200():
    mocker = opbank.mock(path="/personal/v4/*").filter(status(200))
    with meeshkan.intercept_with(response_gen)
        payment_result = my_client.confirm_payment(payment)
    
    assert payment_result.status == PAYMENTS.OK

# Or just use decorators
@meeshkan.intercept_with(mocker=opbank.mock(path="/personal/v4/*").filter(status(200)))
def test_opbank_returns_200(mocker):
    payment_result = my_client.confirm_payment(payment)
    assert payment_result.status == PAYMENTS.OK
    assert mocker.called_once
```

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

## API server testing

Instances of `Model` can be used to generate requests that the API is expected to handle. The following illustrates the basic flow:

```python
from meeshkan.loaders import load_openapi
from meeshkan.models import Model

openapi = load_openapi("openapi.yaml")
model = Model.fromOpenAPI(openapi)

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

***Everything below is experimental***

All the examples above were for testing **stateless** APIs, where every request is independent. This is sufficient for most use cases, but sometimes you need stateful behaviour.

### API client testing

**Requirements**
- *State-dependent draw* strategies
- *Customizable `next_state(state, operation)`*

### API server testing

**Requirements**
- Model that can *drive stateful testing*
- *Commands, preconditions, next_state*
- Postconditions

*Important: Does not require stateful drawing!*

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