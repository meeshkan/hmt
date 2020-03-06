import os
from pathlib import Path

import click
import daemonocle

from meeshkan.server.server.server import MockServer
from .proxy.proxy import RecordProxyRunner
from .utils.routing import PathRouting, HeaderRouting
from ..schemabuilder.update_mode import UpdateMode

LOG_CONFIG = os.path.join(os.path.dirname(__file__), 'logging.yaml')

MOCK_PID = Path.home().joinpath('.meeshkan/mock.pid')
RECORD_PID = Path.home().joinpath('.meeshkan/record.pid')

def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


_common_server_options = [
    click.option('-p', '--port', default="8000", help='Server port.'),
    click.option('-a', '--admin-port', default="8888", help='Admin server port.'),
    click.option('-s', '--specs-dir', default="./specs", help='Directory with OpenAPI schemas.'),
    click.option('-d', '--daemon', is_flag=True, help='Whether to run meeshkan as a daemon.'),
    click.option('-r', '--header-routing', is_flag=True, help='Whether to use a path based routing to a target host.')
]

_record_options = _common_server_options + [
    click.option('-l', '--log-dir', default="./logs", help='API calls logs direcotry'),
    click.option("-m", "--mode", type=click.Choice(['GEN', 'REPLAY', 'MIXED'], case_sensitive=False),
                 default=None, help="Spec building mode.")]

_mock_options = _common_server_options + [
    click.option('-c', '--callback-path', default="./callbacks", help='Directory with configured callbacks.')]


@click.group(invoke_without_command=True)
@add_options(_mock_options)
@click.pass_context
def mock(ctx, callback_path, admin_port, port, specs_dir, header_routing, daemon):
    if ctx.invoked_subcommand is None:
        ctx.forward(start_mock)


@mock.command(name='start')  # type: ignore
@add_options(_mock_options)
def start_mock(callback_path, admin_port, port, specs_dir, header_routing, daemon):
    server = MockServer(callback_path=callback_path, admin_port=admin_port, port=port, specs_dir=specs_dir,
                        routing=HeaderRouting() if header_routing else PathRouting())

    if daemon:
        daemon = daemonocle.Daemon(
            worker=server.run,
            workdir=os.getcwd(),
            pidfile=MOCK_PID,
        )
        daemon.start()
    else:
        server.run()


@mock.command(name='stop')  # type: ignore
def stop_mocking():
    daemon = daemonocle.Daemon(
        pidfile=MOCK_PID,
    )
    daemon.stop()


@mock.command(name='status')  # type: ignore
def status_mocking():
    daemon = daemonocle.Daemon(
        pidfile=MOCK_PID,
    )
    daemon.status()


@click.group(invoke_without_command=True)
@add_options(_record_options)
@click.pass_context
def record(ctx, port, admin_port, log_dir, header_routing, specs_dir, mode, daemon):
    if ctx.invoked_subcommand is None:
        ctx.forward(start_record)


@record.command(name='start')  # type: ignore
@add_options(_record_options)
def start_record(port, admin_port, log_dir, header_routing, specs_dir, mode, daemon):
    proxy_runner = RecordProxyRunner(port=port, admin_port=admin_port, log_dir=log_dir,
                                     routing=HeaderRouting() if header_routing else PathRouting(),
                                     specs_dir=specs_dir, mode=UpdateMode[mode.upper()] if mode else None)
    if daemon:
        daemon = daemonocle.Daemon(
            worker=proxy_runner.run,
            workdir=os.getcwd(),
            pidfile=RECORD_PID,
        )
        daemon.start()
    else:
        proxy_runner.run()


@record.command(name='stop')  # type: ignore
def stop_recording():
    daemon = daemonocle.Daemon(
        pidfile=RECORD_PID,
    )
    daemon.stop()


@record.command(name='status')  # type: ignore
def status_recording():
    daemon = daemonocle.Daemon(
        pidfile=RECORD_PID,
    )
    daemon.status()
