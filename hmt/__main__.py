import asyncio
from typing import Sequence

import click
from openapi_typed_2 import OpenAPIObject, convert_to_openapi
from yaml import safe_load

from .build.builder import BASE_SCHEMA, build_schema_async
from .build.update_mode import UpdateMode
from .config import DEFAULT_SPECS_DIR, setup
from .hmt_types import BuildResultStream
from .logger import get as getLogger
from .prepare import ignore_warnings
from .serve.commands import mock, record
from .sinks import AbstractSink, FileSystemSink
from .sources import AbstractSource, FileSource, KafkaSource
from .sources.kafka import KafkaSourceConfig
from .tutorial import run_tutorial

ignore_warnings()


LOGGER = getLogger(__name__)


def log(*args):
    LOGGER.debug(*args)


@click.group()
@click.version_option()
def cli():
    setup()  # Ensure setup is done before invoking the CLI.


async def write_to_sink(
    result_stream: BuildResultStream, sinks: Sequence[AbstractSink]
):
    try:
        async for result in result_stream:
            for sink in sinks:
                sink.push(result)
    finally:
        LOGGER.debug("Flushing all sinks")
        for sink in sinks:
            sink.flush()


def run_from_source(
    source: AbstractSource,
    mode: UpdateMode,
    starting_spec: OpenAPIObject,
    sinks: Sequence[AbstractSink],
):
    loop = asyncio.get_event_loop()

    if loop.is_closed():
        # Hack to allow running multiple tests that close the event loop
        loop = asyncio.new_event_loop()

    async def run(loop):
        source_stream, source_task = await source.start(loop)
        result_stream = build_schema_async(source_stream, mode, starting_spec)
        sink_task = loop.create_task(write_to_sink(result_stream, sinks))

        if source_task is not None:
            # TODO Kafka source behaves a bit bad at SIG_INT: it does not raise but returns,
            # leaving the sink task to wait for new input that never arrives. Therefore
            # one cannot `await sink_task` here, at least not without timeout
            await source_task
            try:
                await asyncio.wait_for(sink_task, timeout=3.0)
            except asyncio.TimeoutError:
                LOGGER.warn("Timeout on waiting for sink task to finish.")
        else:
            await sink_task

    try:
        loop.run_until_complete(run(loop))
    finally:
        LOGGER.info("Shutting down source")
        source.shutdown()
        loop.close()


@click.command()
@click.option(
    "-i",
    "--input-file",
    required=False,
    type=click.File("rb"),
    help="Input file. Use dash '-' to read from stdin.",
)
# TODO Isn't it a too complicated instruction? Probably, we want to change behavior to os.makedirs()
@click.option(
    "-o",
    "--out",
    required=True,
    default=DEFAULT_SPECS_DIR,
    type=click.Path(exists=False, file_okay=False, writable=True, readable=True),
    help="Output directory. If the directory does not exist, it is created if the parent directory exists.",
)
@click.option(
    "-a",
    "--initial-openapi-spec",
    required=False,
    type=click.File("rb"),
    help="Initial OpenAPI spec.",
)
@click.option(
    "-m",
    "--mode",
    type=click.Choice(["GEN", "REPLAY", "MIXED"], case_sensitive=False),
    default="GEN",
    help="Spec building mode.",
)
@click.option(
    "--source",
    required=False,
    default="file",
    type=str,
    help="Source to read recordings from. For example, 'kafka'",
)
def build(input_file, out, initial_openapi_spec, mode, source):
    """
    Build an OpenAPI specification from HTTP recordings.
    """

    if input_file is not None and source != "file":
        raise Exception("Only specify input-file for --source file")

    sinks = [FileSystemSink(out)]

    if source == "kafka":
        # TODO Kafka configuration
        source = KafkaSource(
            config=KafkaSourceConfig(broker="localhost:9092", topic="http_recordings")
        )
    elif source == "file":
        if input_file is None:
            raise Exception("Option --input-file for source 'file' required.")
        source = FileSource(input_file)
    else:
        raise Exception("Unknown source {}".format(source))

    openapi_spec: OpenAPIObject = BASE_SCHEMA

    if initial_openapi_spec is not None:
        try:
            maybe_openapi = safe_load(initial_openapi_spec.read())
            # will raise if not an API spec
            openapi_spec = convert_to_openapi(maybe_openapi)
        except Exception:
            pass  # just use the initial schema
    run_from_source(source, UpdateMode[mode.upper()], openapi_spec, sinks=sinks)


@click.command()
def tutorial():
    """
    Run the Meeshkan tutorial.
    """
    run_tutorial()


cli.add_command(build)  # type: ignore
cli.add_command(record)  # type: ignore
cli.add_command(mock)  # type: ignore
cli.add_command(tutorial)  # type: ignore

if __name__ == "__main__":
    cli()
