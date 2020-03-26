# Meeshkan model

Every API mocked by Meeshkan is an instance of `Model`. `Model` is essentially a **data generator**. Under the Hood, `Model` class is powered by [Hypothesis](https://hypothesis.readthedocs.io/en/latest/data.html) package for property-based testing. Below, we go through examples of how models can cover different use-cases.

## 1. Testing API clients

### Python

```python
from models import opbank

# Add maps and filters to control generated data
# Type of mocker is `Callable[[Request], Generator[Response]]`
# but it has `map`, `filter`, etc.
@given(mocker=opbank.mock(path="/personal/v4/*").filter(status(500)))
def test_opbank_returns_500(mocker):
    with meeshkan.intercept_with(mocker):  # Intercept HTTP traffic when used as a context manager
        with pytest.raises(PaymentException):
            my_client.confirm_payment(payment)

# The decorator does not really have any purpose here, it's only for readability
@given(mocker=opbank.mock(path="/personal/v4/*").filter(status(200)))
def test_opbank_returns_200(mocker):
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

```Dockerfile
FROM python-3.8.0
RUN pip install meeshkan
# File containing a class inheriting `BaseModel`
ADD models.py 
# Specify path to class
CMD ["meeshkan", "mock", "models:OpBank"]
```

TODO: How to interact with generators? REST API?

### Other languages

TODO: How to interact with the running server? Pyro over socket (HTTP)?

## 2. Testing API server


Example of simple usage:

```python
model = Model.fromOpenAPI(openapi_object)

# Generator of requests
request_gen = model.requests

# Generate example request along with response "context". Context allows validating response.
req, res_ctx = request_gen.example()

# Send request to locally running server
res = req.send("http://localhost:8000")

# Validate response against the context. For example, check that status code is one of those listed in 
res.validate(res_ctx)
```

Stateless property-based testing usage:

```python
model = Model.fromOpenAPI(openapi_object)
@given(req=model.requests)
def test_everything(req):
    req, res_ctx = req
    res = req.send("http://localhost:8000")
    assert res.validate(res_ctx)
```

TODO: Stateful testing?
