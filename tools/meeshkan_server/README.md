# Meeshkan API mocking server
Meeshkan API mocking server is able to record your API traffic in a reverse proxy mode and then produce powerfull mocks out of it.
## Installation
The API mocking server is an additional tool provide alongside Meeshkan CLI tool. 
To install it run:
```bash
pip install meeshkan[server]
```
## Quickstart
1. Start it by running:
```bash
python -m meeshkan_proxy record
```
2. Change external API calls from http(s)://host/path?query=value 
to http://localhost:8899/http(s)/host/path?query=value. For example, 
https://api.imgur.com/3/gallery/search/time/all/1?q=Finland should be changed to
http://localhost:8899/https/api.imgur.com/3/gallery/search/time/all/1?q=Finland
3. Run your scripts.
4. Now you should have the logs folder with jsonl files and the __unmock__ folder with ready openapi schemes. 
5. Restart Meeshkan Server in mocking mode:
```bash
python -m meeshkan_proxy mock
```
6. You don't have to change anything in your client script. It should work with mocks now. You can switch between mocking, recording, accessing real APIs
by switching Meeshkan Proxy modes.
## Common command-line arguments
Following commands are similar for both mock and record modes:
* port -          Server port
* log_dir  -      API calls logs directory
* schema_dir   -  Directory with OpenAPI schemas
* help       -         Full help on command line arguments
* admin_port - Admin server port

## Mocking modes
You may launch meeshkan mocking server in different modes providing mode argument, i.e.:
```bash
python -m meeshkan_proxy mock --mode replay
```
Supported modes are:
* replay - replay recorded scenarios. If a request doesn't match any recorded data, a mock will return an error message/
* gen - generate random data according to a schema on each request. It is suitable to test some corner cases and validate
clients on accordance with OpenAPI schema
* mixed - mixed mode. Return recorded data when possible. Otherwise generate random data.

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

