import json
import logging

import requests

logger = logging.getLogger(__name__)


class ScopeManager:
    def __init__(self):
        self._name = None

    def set(self, name):
        self._name = name

    def get(self):
        return self._name

    def clear(self):
        self._name = None


scope_manager = ScopeManager()
