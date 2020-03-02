# Mocking with Meeshkan

Meeshkan can be used to create a mock server from OpenAPI specifications and optional custom callback scripts.

## The meeshkan mock command

To create a mock server from an OpenAPI spec, use the `meeshkan mock` command.

```bash
$ pip install meeshkan
$ meeshkan mock -i spec_dir/
```

And then, in another terminal window, type:

```bash
$ curl http://localhost:8000/foo -H "Host: my.api.com" -H "X-Meeshkan-Scheme: https"
```

Assuming that the directory `spec_dir/` contains an OpenAPI spec with the server `https://my.api.com`, it will return a mock of the resource `GET /foo`.

More options for the `meeshkan mock` command an be seen by running `meeshkan mock --help`.

## Callbacks

To customize responses a directory containing callbacks can be provided in the `callback-path` argument (default: `./callbacks`).

This directory can contain multiple Python scripts containing callbacks. A callback is a function decorated as 
`tools.meeshkan_server.server.callbacks.callback`, each being mapped to an endpoint by a HTTP method, host and path.

```python
from meeshkan.server.server.callbacks import callback

@callback('meeshkan.com', 'post', '/counter')
def counter_callback(request_body, response_body, storage):
    if 'set' in request_body:
        storage['called'] = request_body['set']
    else:
        storage['called'] = storage.get('called', 0) + 1
    response_body['count'] = storage['called']
    return response_body
```

You may declare callbacks with following function arguments:
* query 
* request_headers
* respone_headers
* request
* response
* storage
* request_body
* response_body

The will be wired automatically.    

Storage is global storage that follows dict syntax. It can storage a global state shared across different endpoints.

You may also provide a format to a callback decorator. The default format is 'json'. If you provide 'text' you'll get strings in request_body and response_body.
```python
from meeshkan.server.server.callbacks import callback

@callback('meeshkan.com', 'post', '/counter', format='text')
def counter_callback(request_body, response_body, storage):
    response_body = 'Response body should be a string'
    return response_body
```
If you have to modify response headers you may provide response type value 'full'. In that case callback should return
full http_types.Response structure instead of body.
```python
from meeshkan.server.server.callbacks import callback
from http_types import Response

@callback('meeshkan.com', 'post', '/counter', response='full')
def counter_callback(request_body, response_body, storage):
    return Response(statusCode=500, bodyAsJson={'message': 'Not ok'},
                                headers={'x-custom-header': 'some value'})
```

### Admin server

An admin server exists at the http://[host]:[admin_port]/admin endpoint. It can be used to reset the callback storage by calling `DELETE http://[host]:[admin_port]/admin/storage`.

## JIT OpenAPI schema manipulations

By default, `meeshkan mock` will serve random data based on the full range of possible outcomes specified in an OpenAPI spec. For example, if an endpoint can serve `200` and `403` responses, Meeshkan will randomly choose between the two.  Sometimes, this type of unpredictability is what you want, ie when doing a smoke test or end-to-end test.  However, other times, you would like to mock a more specific scenario.  For example, you may want an endpoint to _only_ serve 403, or _always_ omit an optional field in a `200` response.

To achieve this, Meeshkan provides a webhook API that will send the incoming request represented using the `http-types` format and the OpenAPI scheams in dictionary format to an endpoint and use the response from the endpoint as the final schema for mocking.  Here is the API for getting, setting, and deleting webhooks.

| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/admin/middleware/rest/pregen/http://localhost:8080` | Notify the server to use the webhook http://localhost:8080. |
| `DELETE` | `/admin/middleware/rest/pregen/http://localhost:8080` | Delete the webhook http://localhost:8080. |
| `GET` | `/admin/middleware/rest/pregen` | Get all webhooks that have been registered. |
| `DELETE` | `/admin/middleware/rest/pregen` | Delete all registered webhooks. |

The webhook must accept a `POST` request for an object in the following format:

```json
{
    "request": { ...incoming request... },
    "schemas": { ...openapi schemas... }
}
```

And return the `schemas` object - that is, a dictionary of OpenAPI schemas.

