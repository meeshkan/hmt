from meeshkan.schemabuilder.result import BuildResult
import click
import json
from http_types import RequestResponseBuilder

from .schemabuilder import build_schema_online
from .schemabuilder.writer import write_build_result
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
@click.option("-o", "--out", required=False, default='out', type=click.Path(exists=False, file_okay=False, writable=True, readable=True), help="Output folder. If the folder does not exist, the parent directory must exist.")
def build(input_file, out):
    """
    Build OpenAPI schema from recordings.
    """
    requests = (RequestResponseBuilder.from_dict(
        json.loads(line)) for line in input_file)

    schema = build_schema_online(requests)

    build_result = BuildResult(openapi=schema)

    log("Result: %s", json.dumps(schema))
    write_build_result(out, build_result)


cli.add_command(build)  # type: ignore

if __name__ == '__main__':
    cli()
