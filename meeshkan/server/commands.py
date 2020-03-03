import os
from pathlib import Path

import click
import daemonocle

from meeshkan.server.server.server import MockServer
from .proxy.proxy import RecordProxyRunner
from .utils.routing import PathRouting, HeaderRouting
from ..schemabuilder.update_mode import UpdateMode

LOG_CONFIG = os.path.join(os.path.dirname(__file__), 'logging.yaml')


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


@click.group()
def mock():
    pass


@mock.command(name='start') # type: ignore
@click.option('-c', '--callback-path', default="./callbacks", help='Directory with configured callbacks.')
@add_options(_common_server_options)
def start_mock(callback_path, admin_port, port, specs_dir, header_routing, daemon):
    """
    Run a mock server.
    """
    server = MockServer(callback_path=callback_path, admin_port=admin_port, port=port, specs_dir=specs_dir,
                        routing=HeaderRouting() if header_routing else PathRouting())

    if daemon:
        daemon = daemonocle.Daemon(
            worker=server.run,
            workdir=os.getcwd(),
            pidfile=Path.home().joinpath('.meeshkan/mock.pid'),
        )
        daemon.start()
    else:
        server.run()


@mock.command(name='stop') # type: ignore
def stop_mocking():
    daemon = daemonocle.Daemon(
        pidfile=Path.home().joinpath('.meeshkan/mock.pid'),
    )
    daemon.stop()


@mock.command(name='status') # type: ignore
def status_mocking():
    daemon = daemonocle.Daemon(
        pidfile=Path.home().joinpath('.meeshkan/mock.pid'),
    )
    daemon.status()


@click.group()
def record():
    pass


@record.command(name='start') # type: ignore
@click.option('-l', '--log-dir', default="./logs", help='API calls logs direcotry')
@click.option("-m", "--mode", type=click.Choice(['GEN', 'REPLAY', 'MIXED'], case_sensitive=False),
              default=None, help="Spec building mode.")
@add_options(_common_server_options)
def start_record(port, admin_port, log_dir, header_routing, specs_dir, mode, daemon):
    proxy_runner = RecordProxyRunner(port=port, admin_port=admin_port, log_dir=log_dir,
                                     routing=HeaderRouting() if header_routing else PathRouting(),
                                     specs_dir=specs_dir, mode=UpdateMode[mode.upper()] if mode else None)
    if daemon:
        daemon = daemonocle.Daemon(
            worker=proxy_runner.run,
            workdir=os.getcwd(),
            pidfile=Path.home().joinpath('.meeshkan/record.pid'),
        )
        daemon.start()
    else:
        proxy_runner.run()


@record.command(name='stop') # type: ignore
def stop_recording():
    daemon = daemonocle.Daemon(
        pidfile=Path.home().joinpath('.meeshkan/record.pid'),
    )
    daemon.stop()


@record.command(name='status') # type: ignore
def status_recording():
    daemon = daemonocle.Daemon(
        pidfile=Path.home().joinpath('.meeshkan/record.pid'),
    )
    daemon.status()
