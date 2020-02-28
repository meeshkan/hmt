# Mocking with Meeshkan

Meeshkan can be used to creae a mock server from an OpenAPI spec using.

## The meeshkan mock command

To create a mock server from an OpenAPI spec, use the `meeshkan mock` command.

```bash
$ pip install meeshkan
$ meeshkan mock -i spec_dir/
```

And then, in another terminal window, type:

```bash
$ curl http://localhost:8000/foo -H '{"Host": "my.api.com", "X-Meeshkan-Schema": "https"}'
```

Assuming that the directory `spec_dir/` contains an OpenAPI spec with the server `https://my.api.com`, it will return a mock of the resource `GET /foo`.

More options for the `meeshkan mock` command an be seen by running `meeshkan mock --help`.

## Custom middleware

## JIT OpenAPI schema manipulations