from dataclasses import dataclass
from .scope import ScopeManager
from typing import Optional, Sequence
from http_types import Request, Response
import time


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

    def __init__(self, scope_manager: ScopeManager):
        self._scope_manager = scope_manager
        self._interactions = []

    def put(self, request: Request, response: Response):
        self._interactions = [
            *self._interactions,
            LoggedHttpExchange(
                request=request,
                response=response,
                meta=MeeshkanMeta(
                    timestamp=int(time.time() * 1000), scope=ScopeManager.get()
                ),
            ),
        ]
