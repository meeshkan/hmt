# Recording with Meeshkan

Meeshkan can be used to record HTTP API traffic in a format that `meeshkan build` can understand.  This format serializes JSON objects in the [`http-types`](https://github.com/meeshkan/http-types) format written to a [`.jsonl`](https://jsonlines.org) file.

## The meeshkan record command

To start a Meeshkan server that will record HTTP API traffic, use the `meeshkan record` command.

```
$ pip install meeshkan
$ meeshkan record
```

By default, `meeshkan record` records all traffic to a folder called `logs`.  You can change the recording directory using the `-l` flag, ie `-l some_other_directory`. For a full list of recording options, type `meeshkan record --help`.

## Path versus header routing

By default, Meeshkan uses **path routing** to intercept HTTP API calls.  Path routing is done by appending the URL you wish to call to the URL of the recording server.

```bash
$ meeshkan record
```
And then, in another terminal window, type:

```bash
$ curl http://localhost:8000/http://time.jsontest.com
```

Meeshkan will automatically make an API call using the URL in the path - in this case, [http://time.jsontest.com](http://time.jsontest.com), and return the response from the called API.

Alternatively, you can run Meeshkan in **header** mode, which uses the host and optionally the schema reported in the header.

```bash
$ meeshkan record -r
```
And then, in another terminal window

```bash
$ curl http://localhost:8000/api/v2/pokemon/ditto -H '{"Host":"pokeapi.co", "X-Meeshkan-Schema": "https" }'
```

This instructs meeshkan to call pokeapi.co and to use the HTTPS protocol.

## Ecosystem

In addition to using Meeshkan to record, there is a growing ecosystem of projects that one can use to create `.jsonl` files in the [`http-types`](https://github.com/meeshkan/http-types).  Here are some other ways one can create `.jsonl` files of server recordings that are consumable by `meeshkan build`.

### Client libraries

You can use one of the [`http-types`](https://github.com/meeshkan/http-types) client libraries to write recorded traffic as `.jsonl` files.  Here are the libraries that currently exist:

- [js-http-types](https://github.com/meeshkan/js-http-types) 
- [java-http-types](https://github.com/meeshkan/java-http-types) 
- [py-http-types](https://github.com/meeshkan/py-http-types) 

In the future, we hope to build client libraries in C#, C++, Go, Rust, Brainfuck, Haskell and OCaml.

Below is an example of how one can use `py-http-types` to record HTTP traffic to `.jsonl` files directly in Python.

```python
import urllib.request as request
import json
from io import StringIO
from http_types.utils import HttpExchange, RequestBuilder, ResponseBuilder, HttpExchangeWriter

reqs = [request.Request('http://time.jsontest.com') for x in range(10)]
ress = [request.urlopen(x) for x in reqs]
exchanges = [HttpExchange(
            request=RequestBuilder.from_urllib_request(req),
            response=ResponseBuilder.from_http_client_response(res)
        ) for req, res in zip(reqs, ress)]

sink = StringIO()
for exchange in exchanges:
    HttpExchangeWriter(sink).write(exchange)

sink.seek(0)

with open('recordings.jsonl', 'w') as recording_file:
    recording_file.write(''.join([line for line in sink]))
```

### Integrations

We plan on maintaining middleware and plugins for a variety of projects.  Below is a list of integrations that exist or are in development.

| Integration | Description | Status |
| ----------- | ----------- | ------ |
| [`express-middleware`](https://github.com/meeshkan/express-middleware) | Log files from express apps using a variety of transport layers, including the file system and Apache Kafka. | Stable |
| `wireshark` | Run `meeshkan convert my-file.pcap` to convert a Wireshark `.pcap` file to `http-types` format. | Stable |
| Kong plugin | Log requests and responses to the Kong API Gateway using a variety of transport layers, including the file system and Apache Kafka. | In development |
| AWS API Gateway Plugin | Log requests and responses to the AWS API Gateway using a variety of transport layers, including the file system and Apache Kafka. | In development |
| Apigee Plugin | Log requests and responses to the Apigee API Gateway using a variety of transport layers, including the file system and Apache Kafka. | In development |