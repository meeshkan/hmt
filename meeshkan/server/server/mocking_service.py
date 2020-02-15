import json
import logging
import importlib.util

from http_types import Request, Response
from .callbacks import callback_manager
from .response_matcher import ResponseMatcher

logger = logging.getLogger(__name__)

class MockingService:
    def __init__(self, response_matcher: ResponseMatcher):
        self._response_matcher = response_matcher

    def match(self, request: Request) -> Response:
        logger.debug(request)
        return callback_manager(request, self._response_matcher.get_response(request))

