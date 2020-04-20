import json
import os
import time
from dataclasses import dataclass
from typing import Optional, Sequence

from http_types import HttpExchange, HttpExchangeWriter, Request, Response

from .scope import Scope


@dataclass
class MeeshkanMeta:
    timestamp: int
    scope: Optional[str]


@dataclass
class LoggedHttpExchange:
    request: Request
    response: Response
    meta: MeeshkanMeta


class AbstractSink:
    def write(self, interactions):
        pass


class NoSink(AbstractSink):
    def write(self, interactions):
        pass


class FileSink(AbstractSink):
    def __init__(self, log_dir: str):
        self._dir = log_dir
        if not os.path.exists(self._dir):
            os.mkdir(self._dir)
        self._log_file_name = "%d.log.json" % int(time.time() * 1000)

    def write(self, interactions):
        with open(os.path.join(self._dir, self._log_file_name), "w") as logfile:
            logfile.write(json.dumps(interactions, indent=2))


class Log:
    _interactions: Sequence[LoggedHttpExchange]

    def __init__(self, scope: Scope, sink: Optional[AbstractSink] = None):
        self._scope = scope
        self._sink = sink
        self._interactions = []
        self._interactions_as_json = []
        self._log_file_name = "%d.log.json" % int(time.time() * 1000)

    def put(self, request: Request, response: Response):
        self._interactions = [
            *self._interactions,
            LoggedHttpExchange(
                request=request,
                response=response,
                meta=MeeshkanMeta(
                    timestamp=int(time.time() * 1000), scope=self._scope.get()
                ),
            ),
        ]
        exchange = HttpExchangeWriter.to_dict(
            HttpExchange(request=request, response=response,)
        )
        interaction = {
            **exchange,
            "meta": {
                "timestamp": self._interactions[-1].meta.timestamp,
                **(
                    {"scope": self._interactions[-1].meta.scope}
                    if self._interactions[-1].meta.scope is not None
                    else {}
                ),
            },
        }

        self._interactions_as_json = [*self._interactions_as_json, interaction]
        if self._sink is not None:
            self._sink.write(self._interactions_as_json)
