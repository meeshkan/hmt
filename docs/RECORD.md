# Recording with HMT

HMT can be used to record HTTP API traffic in a format that `hmt build` can understand.  This format serializes JSON objects in the [`http-types`](https://github.com/hmt/http-types) format written to a [`.jsonl`](https://jsonlines.org) file. By default, this file will be called `{hostname}-recordings.jsonl` with `{hostname}` referring to your API's host URL. 

## What's in this document

- [The `hmt record` command](#the-hmt-record-command)
- [Path vs. header routing](#path-vs-header-routing)
    - [Path routing](#path-routing)
    - [Header routing](#header-routing)
- [Daemon mode](#daemon-mode)
- [Ecosystem](#ecosystem)
    - [Client libraries](#client-libraries)
    - [Integrations](#integrations)
- [Next up: Building with HMT](#next-up-building-with-hmt)

## The `hmt record` command

To start a HMT server that will record HTTP API traffic, use the `hmt record` command:

```bash
$ hmt record
```

This starts HMT as a reverse proxy on the default port of `8000`. Running `hmt record` will also generate two directories: `logs` and `specs`.

By default, `hmt record` records all traffic to the `logs` directory.  You can change the recording directory using the `--log_dir` flag, i.e. `--log_dir path/to/directory`. 

> More options for the `hmt record` command an be seen by running `hmt record --help`.

To stop HMT without losing your any of your data, type `Ctrl + C` or another `kill` command.  

## Path vs. header routing

### Path routing

By default, HMT uses **path routing** to intercept HTTP API calls. Path routing is done by appending the URL you wish to call to the URL of the recording server.

```bash
$ hmt record
```

Keep this running. Then, in another terminal window, you can use HMT as a proxy with [curl](https://curl.haxx.se/):

```bash
$ curl http://localhost:8000/http://time.jsontest.com
```

HMT will automatically make an API call using the URL in the path - in this case, [http://time.jsontest.com](http://time.jsontest.com) - and return the response from the called API.

### Header routing

Alternatively, you can run HMT in **header** mode, which uses the host and optionally the schema reported in the header.

```bash
$ hmt record --header_routing
```
Keep this running. Then, in another terminal window, run:

```bash
$ curl http://localhost:8000/api/v2/pokemon/ditto -H "Host: pokeapi.co" -H "X-HMT-Scheme: https"
```

This instructs hmt to call the [Pokemon API](pokeapi.co) and use the HTTPS protocol.

## Daemon mode

HMT can be launched as a [daemon](https://docs.docker.com/engine/reference/commandline/dockerd/) by providing the `--daemon` flag to the `hmt record` command:

```bash
$ hmt record --daemon
```

_Note: All other command line arguments remain the same._

To stop your HMT daemon, run:

```bash
$ hmt record stop
```

## Ecosystem

In addition to using HMT to record, there is a growing ecosystem of projects that one can use to create `.jsonl` files in the [`http-types`](https://github.com/hmt/http-types).  

Here are some other ways that you can create `.jsonl` files of server recordings that are consumable by `hmt build`.

### Client libraries

You can use one of the [`http-types`](https://github.com/hmt/http-types) client libraries to write recorded traffic as `.jsonl` files. 

Here are the libraries that currently exist:

- [js-http-types](https://github.com/hmt/js-http-types) 
- [java-http-types](https://github.com/hmt/java-http-types) 
- [py-http-types](https://github.com/hmt/py-http-types) 

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
| [`express-middleware`](https://github.com/hmt/express-middleware) | Log files from express apps using a variety of transport layers, including the file system and Apache Kafka. | Stable |
| `wireshark` | Convert a Wireshark `.pcap` file to `http-types` format. | Stable |
| Kong plugin | Log requests and responses to the Kong API Gateway using a variety of transport layers, including the file system and Apache Kafka. | In development |
| AWS API Gateway Plugin | Log requests and responses to the AWS API Gateway using a variety of transport layers, including the file system and Apache Kafka. | In development |
| Apigee Plugin | Log requests and responses to the Apigee API Gateway using a variety of transport layers, including the file system and Apache Kafka. | In development |

## Next up: Building with HMT

After you've recorded your API traffic with `hmt record`, you can use that data to to build an OpenAPI specification via the HMT CLI. 

To learn how, visit our [building documentation](./docs/BUILD.md).