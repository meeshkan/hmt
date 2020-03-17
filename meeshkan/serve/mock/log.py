import time
from dataclasses import dataclass
from typing import Optional, Sequence

from http_types import Request, Response

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


class Log:
    _interactions: Sequence[LoggedHttpExchange]

    def __init__(self, scope: Scope):
        self._scope = scope
        self._interactions = []

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
