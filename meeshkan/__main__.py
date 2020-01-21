import click
from .schemabuilder import build_schema_online
import json
from http_types import RequestResponseBuilder
from .logger import get as getLogger
from yaml import dump
from typing import cast


logger = getLogger(__name__)


def log(*args):
    logger.debug(*args)


@click.group()
def cli():
    pass


@click.command()
@click.option("-i", "--input-file", required=True, type=click.File('rb'), help="Input file. Use dash '-' to read from stdin.")
@click.option("-o", "--out", required=False, default=None, type=click.Path(exists=False), help="Output file. If omitted, output is written to stdout.")
def build(input_file, out):
    """
    Build OpenAPI schema from recordings.
    """
    requests = []

    requests = (RequestResponseBuilder.from_dict(
        json.loads(line)) for line in input_file)

    schema = build_schema_online(requests)

    schema_yaml = cast(str, dump(schema))
    log("Result:\n%s", schema_yaml)

    if out is not None:
        with open(out, 'wb') as f:
            log("Writing to: %s\n", out)
            f.write(schema_yaml.encode())
    else:
        print(schema_yaml)


cli.add_command(build)  # type: ignore

if __name__ == '__main__':
    cli()
