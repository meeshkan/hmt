# Recording with Meeshkan

Meeshkan can be used to transform HTTP traf

## Ecosystem

In addition to using Meeshkan to record, there is a growing ecosystem of projects that one can use to create `.jsonl` files in the [`http-types`](https://github.com/meeshkan/http-types).  Here are some other ways one can create `.jsonl` files of server recordings that are consumable by `meeshkan build`.

### Client libraries

You can use one of the [`http-types`](https://github.com/meeshkan/http-types) client libraries to write recorded traffic as `.jsonl` files.  Here are the libraries that currently exist:

- js-http-types
- java-http-types
- python-http-types

In the future, we hope to build client libraries in C#, C++, Go, Rust, Brainfuck, Haskell and OCaml.

Below is an example of how one can use `py-http-types` to record HTTP traffic to `.jsonl` files directly in Python.

### Integrations

We plan on maintaining middleware and plugins for a variety of projects.  Below is a list of integrations that exist or are in development.

| Integration | Description | Status |
| ----------- | ----------- | ------ |
| [`express-middleware`](https://github.com/meeshkan/express-middleware) | Log files from express apps using a variety of transport layers, including the file system and Apache Kafka. | Stable |
| `wireshark` | Run `meeshkan convert my-file.pcap` to convert a Wireshark `.pcap` file to `http-types` format. | Stable |
| Kong plugin | Log requests and responses to the Kong API Gateway using a variety of transport layers, including the file system and Apache Kafka. | In development |
| AWS API Gateway Plugin | Log requests and responses to the AWS API Gateway using a variety of transport layers, including the file system and Apache Kafka. | In development |
| Apigee Plugin | Log requests and responses to the Apigee API Gateway using a variety of transport layers, including the file system and Apache Kafka. | In development |