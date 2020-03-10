import os
import sys
import logging
from pathlib import Path

import click

IS_WINDOWS = os.name == 'nt'

from meeshkan.serve.mock.server import MockServer
from .record.proxy import RecordProxyRunner
from .utils.routing import PathRouting, HeaderRouting
from ..build.update_mode import UpdateMode
from ..config import DEFAULT_SPECS_DIR

LOG_CONFIG = os.path.join(os.path.dirname(__file__), 'logging.yaml')
MOCK_PID = Path.home().joinpath('.meeshkan/mock.pid')
RECORD_PID = Path.home().joinpath('.meeshkan/record.pid')

logger = logging.getLogger(__name__)

def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options

def run_with_exception_handling(runnable, verbose):
    try:
        runnable.run()
    except Exception as e:
        logger.critical(e, exc_info=verbose)
        sys.exit(1)

_common_server_options = [
    click.option('-p', '--port', default="8000", help='Server port.'),
    click.option('-a', '--admin-port', default="8888", help='Admin server port.'),
    click.option('-s', '--specs-dir', default=DEFAULT_SPECS_DIR, help='Directory with OpenAPI schemas.'),
    click.option('-d', '--daemon', is_flag=True, help='Whether to run meeshkan as a daemon.'),
    click.option('-r', '--header-routing', is_flag=True, help='Whether to use a path based routing to a target host.'),
    click.option('--verbose', is_flag=True, help='If logging should be verbose.')
]

_record_options = _common_server_options + [
    click.option('-l', '--log-dir', default="./logs", help='API calls logs direcotry'),
    click.option("-m", "--mode", type=click.Choice(['GEN', 'REPLAY', 'MIXED'], case_sensitive=False),
                 default=None, help="Spec building mode.")]

_mock_options = _common_server_options + [
    click.option('-c', '--callback-dir', default="./callbacks", help='Directory with configured callbacks.')]


@click.group(invoke_without_command=True)
@add_options(_mock_options)
@click.pass_context
def mock(ctx, callback_dir, admin_port, port, specs_dir, header_routing, daemon, verbose):
    if ctx.invoked_subcommand is None:
        ctx.forward(start_mock)


@mock.command(name='start')  # type: ignore
@add_options(_mock_options)
def start_mock(callback_dir, admin_port, port, specs_dir, header_routing, daemon, verbose):
    server = MockServer(callback_dir=callback_dir, admin_port=admin_port, port=port, specs_dir=specs_dir,
                        routing=HeaderRouting() if header_routing else PathRouting())

    if daemon and (not IS_WINDOWS):
        import daemonocle
        daemon = daemonocle.Daemon(
            worker=server.run,
            workdir=os.getcwd(),
            pidfile=MOCK_PID,
        )
        daemon.start()
    else:
        run_with_exception_handling(server, verbose)


@mock.command(name='stop')  # type: ignore
def stop_mocking():
    if not IS_WINDOWS:
        import daemonocle
        daemon = daemonocle.Daemon(
            pidfile=MOCK_PID,
        )
        daemon.stop()


@mock.command(name='status')  # type: ignore
def status_mocking():
    if not IS_WINDOWS:
        import daemonocle
        daemon = daemonocle.Daemon(
            pidfile=MOCK_PID,
        )
        daemon.status()


@click.group(invoke_without_command=True)
@add_options(_record_options)
@click.pass_context
def record(ctx, port, admin_port, log_dir, header_routing, specs_dir, mode, daemon, verbose):
    if ctx.invoked_subcommand is None:
        ctx.forward(start_record)


@record.command(name='start')  # type: ignore
@add_options(_record_options)
def start_record(port, admin_port, log_dir, header_routing, specs_dir, mode, daemon, verbose):
    proxy_runner = RecordProxyRunner(port=port, admin_port=admin_port, log_dir=log_dir,
                                     routing=HeaderRouting() if header_routing else PathRouting(),
                                     specs_dir=specs_dir, mode=UpdateMode[mode.upper()] if mode else None)
    if daemon and (not IS_WINDOWS):
        import daemonocle
        daemon = daemonocle.Daemon(
            worker=proxy_runner.run,
            workdir=os.getcwd(),
            pidfile=RECORD_PID,
        )
        daemon.start()
    else:
        run_with_exception_handling(proxy_runner, verbose)


@record.command(name='stop')  # type: ignore
def stop_recording():
    if not IS_WINDOWS:
        import daemonocle
        daemon = daemonocle.Daemon(
            pidfile=RECORD_PID,
        )
        daemon.stop()


@record.command(name='status')  # type: ignore
def status_recording():
    if not IS_WINDOWS:
        import daemonocle
        daemon = daemonocle.Daemon(
            pidfile=RECORD_PID,
        )
        daemon.status()
