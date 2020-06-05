# Mocking with HMT

HMT can be used to create a mock server from OpenAPI specifications and optional custom callback scripts.

## What's in this document

  - [The `hmt mock` command](#the-hmt-mock-command)
    - [Making requests](#making-requests)
  - [Daemon mode](#daemon-mode)
  - [Callbacks](#callbacks)
    - [Function arguments](#function-arguments)
    - [Formats](#formats)
    - [Response types](#response-types)
  - [Admin server](#admin-server)
  - [JIT OpenAPI schema manipulations](#jit-openapi-schema-manipulations)

## The `hmt mock` command

To create your mock server, use the `hmt mock` command and include the path to the directory that your OpenAPI spec is in:

```bash
$ hmt mock path/to/dir/
```

Alternatively, you can also designate a path to one specific file:

```bash
$ hmt mock path/to/openapi.yml
```

### Making requests

Keep this running. Then, in another terminal window, make a request using [curl](https://curl.haxx.se/):

```bash
$ curl http://localhost:8000/https://my.api.com/users
```

Assuming that your OpenAPI spec has the server `https://my.api.com`, this will return a mock of the resource `GET /users`.

> More options for the `hmt mock` command an be seen by running `hmt mock --help`.

## Daemon mode

HMT can be launched as a [daemon](https://docs.docker.com/engine/reference/commandline/dockerd/) by providing the `--daemon` flag to the `hmt mock` command:

```bash
$ hmt mock --daemon
```

_Note: All other command line arguments stay the same._

To stop your HMT daemon, run:

```bash
$ hmt mock --kill
```

## Callbacks

To customize responses, a directory containing callbacks can be provided with the `--callback_path` flag:

```bash
$ hmt mock --callback_path path/to/directory
```

This directory can contain multiple Python scripts containing callbacks. A callback is a function decorated as 
`hmt_server.server.callbacks.callback`, each being mapped to an endpoint by a HTTP method, host and path.

```python
from hmt.server.server.callbacks import callback

@callback('hmt.com', 'post', '/counter')
def counter_callback(request_body, response_body, storage):
    if 'set' in request_body:
        storage['called'] = request_body['set']
    else:
        storage['called'] = storage.get('called', 0) + 1
    response_body['count'] = storage['called']
    return response_body
```

### Function arguments

You can declare callbacks with following function arguments:
* `query` 
* `request_headers`
* `respone_headers`
* `request`
* `response`
* `storage`
* `request_body`
* `response_body`

These function arguments will be wired automatically.    

_Note: `storage` is global storage that follows dict syntax. It can storage a global state shared across different endpoints._

### Formats

You may also provide a `format` to a callback decorator. The default `format` is `'json'`. But, for example, if you provide `'text'` you'll get strings in request_body and response_body:

```python
from hmt.server.server.callbacks import callback

@callback('hmt.com', 'post', '/counter', format='text')
def counter_callback(request_body, response_body, storage):
    response_body = 'Response body should be a string'
    return response_body
```

### Response types

If you have to modify response headers, you can provide a `response` type value of `'full'`. In that case, the callback should return the full `http_types.Response` structure instead of body.

```python
from hmt.server.server.callbacks import callback
from http_types import Response

@callback('hmt.com', 'post', '/counter', response='full')
def counter_callback(request_body, response_body, storage):
    return Response(statusCode=500, bodyAsJson={'message': 'Not ok'},
                                headers={'x-custom-header': 'some value'})
```

## Admin server

An admin server exists at the `http://[host]:[admin_port]/admin endpoint`. 

It can be used to reset the callback storage by calling `DELETE http://[host]:[admin_port]/admin/storage`.

## JIT OpenAPI schema manipulations

By default, `hmt mock` will serve random data based on the full range of possible outcomes specified in an OpenAPI spec. For example, if an endpoint can serve `200` and `403` responses, HMT will randomly choose between the two. 

Sometimes, this type of unpredictability is what you want. For instance, when doing a smoke test or end-to-end test. 

However, other times, you would like to mock a more specific scenario. For example, you may want an endpoint to _only_ serve 403, or _always_ omit an optional field in a `200` response.

To achieve this, HMT provides a webhook API that will send the incoming request represented using the [`http-types`](https://github.com/meeshkan/http-types/) format and the OpenAPI scheams in dictionary format to an endpoint. Then, it will use the response from the endpoint as the final schema for mocking.

Here is the API for getting, setting, and deleting webhooks:

| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/admin/middleware/rest/pregen/http://localhost:8080` | Notify the server to use the webhook http://localhost:8080. |
| `DELETE` | `/admin/middleware/rest/pregen/http://localhost:8080` | Delete the webhook http://localhost:8080. |
| `GET` | `/admin/middleware/rest/pregen` | Get all webhooks that have been registered. |
| `DELETE` | `/admin/middleware/rest/pregen` | Delete all registered webhooks. |

The webhook must accept a `POST` request for an object in the following format. Then, it should return the `schemas` object - that is, a dictionary of OpenAPI schemas.

```json
{
    "request": { ...incoming request... },
    "schemas": { ...openapi schemas... }
}
```
