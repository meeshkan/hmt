import click
import json
from http_types import RequestResponseBuilder
from yaml import dump
from typing import cast

from .schemabuilder import build_schema_online
from .config import setup
from .logger import get as getLogger


LOGGER = getLogger(__name__)


def log(*args):
    LOGGER.debug(*args)


@click.group()
def cli():
    """
    Meeshkan CLI.
    """
    setup()  # Ensure setup is done before invoking the CLI.


@click.command()
@click.option("-i", "--input-file", required=True, type=click.File('rb'), help="Input file. Use dash '-' to read from stdin.")
@click.option("-o", "--out", required=False, default=None, type=click.Path(exists=False), help="Output file. If omitted, output is written to stdout.")
def build(input_file, out):
    """
    Build OpenAPI schema from recordings.
    """
    requests = (RequestResponseBuilder.from_dict(
        json.loads(line)) for line in input_file)

    schema = build_schema_online(requests)

    schema_yaml = cast(str, dump(schema))
    log("Result: %s", json.dumps(schema))

    if out is not None:
        with open(out, 'wb') as f:
            log("Writing to: %s\n", out)
            f.write(schema_yaml.encode())
    else:
        print(schema_yaml)


cli.add_command(build)  # type: ignore

if __name__ == '__main__':
    cli()
