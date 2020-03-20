# Recording with Meeshkan

Meeshkan can be used to record HTTP API traffic in a format that `meeshkan build` can understand.  This format serializes JSON objects in the [`http-types`](https://github.com/meeshkan/http-types) format written to a [`.jsonl`](https://jsonlines.org) file. By default, this file will be called `{hostname}-recordings.jsonl` with `{hostname}` referring to your API's host URL. 

## What's in this document

- [The `meeshkan record` command](#the-meeshkan-record-command)
- [Path vs. header routing](#path-vs-header-routing)
    - [Path routing](#path-routing)
    - [Header routing](#header-routing)
- [Daemon mode](#daemon-mode)
- [Ecosystem](#ecosystem)
    - [Client libraries](#client-libraries)
    - [Integrations](#integrations)
- [Next up: Building with Meeshkan](#next-up-building-with-meeshkan)

## The `meeshkan record` command

To start a Meeshkan server that will record HTTP API traffic, use the `meeshkan record` command:

```bash
$ meeshkan record
```

This starts Meeshkan as a reverse proxy on the default port of `8000`. Running `meeshkan record` will also generate two directories: `logs` and `specs`.

By default, `meeshkan record` records all traffic to the `logs` directory.  You can change the recording directory using the `--log_dir` flag, i.e. `--log_dir path/to/directory`. 

> More options for the `meeshkan record` command an be seen by running `meeshkan record --help`.

To stop Meeshkan without losing your any of your data, type `Ctrl + C` or another `kill` command.  

## Path vs. header routing

### Path routing

By default, Meeshkan uses **path routing** to intercept HTTP API calls. Path routing is done by appending the URL you wish to call to the URL of the recording server.

```bash
$ meeshkan record
```

Keep this running. Then, in another terminal window, you can use Meeshkan as a proxy with [curl](https://curl.haxx.se/):

```bash
$ curl http://localhost:8000/http://time.jsontest.com
```

Meeshkan will automatically make an API call using the URL in the path - in this case, [http://time.jsontest.com](http://time.jsontest.com) - and return the response from the called API.

### Header routing

Alternatively, you can run Meeshkan in **header** mode, which uses the host and optionally the schema reported in the header.

```bash
$ meeshkan record --header_routing
```
Keep this running. Then, in another terminal window, run:

```bash
$ curl http://localhost:8000/api/v2/pokemon/ditto -H "Host: pokeapi.co" -H "X-Meeshkan-Scheme: https"
```

This instructs meeshkan to call the [Pokemon API](pokeapi.co) and use the HTTPS protocol.

## Daemon mode

Meeshkan can be launched as a [daemon](https://docs.docker.com/engine/reference/commandline/dockerd/) by providing the `--daemon` flag to the `meeshkan record` command:

```bash
$ meeshkan record --daemon
```

_Note: All other command line arguments remain the same._

To stop your Meeshkan daemon, run:

```bash
$ meeshkan record stop
```

## Ecosystem

In addition to using Meeshkan to record, there is a growing ecosystem of projects that one can use to create `.jsonl` files in the [`http-types`](https://github.com/meeshkan/http-types).  

Here are some other ways that you can create `.jsonl` files of server recordings that are consumable by `meeshkan build`.

### Client libraries

You can use one of the [`http-types`](https://github.com/meeshkan/http-types) client libraries to write recorded traffic as `.jsonl` files. 

Here are the libraries that currently exist:

- [js-http-types](https://github.com/meeshkan/js-http-types) 
- [java-http-types](https://github.com/meeshkan/java-http-types) 
- [py-http-types](https://github.com/meeshkan/py-http-types) 

In the future, we hope to build client libraries in C#, C++, Go, Rust, Brainfuck, Haskell and OCaml.

The following code snippet is an example of how you can use `py-http-types` to record HTTP traffic to `.jsonl` files directly in Python:

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

We plan on maintaining middleware and plugins for a variety of projects. 

Here is a list of integrations that exist or are in development:

| Integration | Description | Status |
| ----------- | ----------- | ------ |
| [`express-middleware`](https://github.com/meeshkan/express-middleware) | Log files from express apps using a variety of transport layers, including the file system and Apache Kafka. | Stable |
| `wireshark` | Convert a Wireshark `.pcap` file to `http-types` format. | Stable |
| Kong plugin | Log requests and responses to the Kong API Gateway using a variety of transport layers, including the file system and Apache Kafka. | In development |
| AWS API Gateway Plugin | Log requests and responses to the AWS API Gateway using a variety of transport layers, including the file system and Apache Kafka. | In development |
| Apigee Plugin | Log requests and responses to the Apigee API Gateway using a variety of transport layers, including the file system and Apache Kafka. | In development |

## Next up: Building with Meeshkan

After you've recorded your API traffic with `meeshkan record`, you can use that data to to build an OpenAPI specification via the Meeshkan CLI. 

To learn how, visit our [building documentation](./docs/BUILD.md).