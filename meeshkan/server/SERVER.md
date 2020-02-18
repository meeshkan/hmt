# Meeshkan API mocking server

Meeshkan API mocking server is able to record your API traffic in a reverse proxy mode and then produce powerful mocks out of it.

This document describes some advanced usage features of the server. For basic usage, see the [Meeshkan](../../README.md) README.

## Defining callbacks
A directory containing callbacks can be provided in callback_path argument. The default is:
```bash
python -m meeshkan_proxy mock --callback_path ./callbacks

```
A directory can contain multiple Python scripts. A callback is a function with decorated as 
tools.meeshkan_server.server.callbacks.callback. Each callback is mapped to an endpoint by providing an HTTP method, a host, and a path.
```python
from tools.meeshkan_server.server.callbacks import callback

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
from tools.meeshkan_server.server.callbacks import callback

@callback('meeshkan.com', 'post', '/counter', format='text')
def counter_callback(request_body, response_body, storage):
    response_body = 'Response body should be a string'
    return response_body
```
If you have to modify response headers you may provide response type value 'full'. In that case callback should return
full http_types.Response structure instead of body.
```python
from tools.meeshkan_server.server.callbacks import callback
from http_types import Response

@callback('meeshkan.com', 'post', '/counter', response='full')
def counter_callback(request_body, response_body, storage):
    return Response(statusCode=500, bodyAsJson={'message': 'Not ok'},
                                headers={'x-custom-header': 'some value'})
```
## Admin server
The admin server works under the http://[host]:[admin_port]/admin endpoint. It allows to manage the Meeshkan server 
in runtime using provided REST API.
### Reset storage
Reset state of embedded storage.

* **URL**

/storage

* **Method:**
  
`DELETE` 

