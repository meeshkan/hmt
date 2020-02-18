import logging

logger = logging.getLogger(__name__)


class StorageManager:
    def __init__(self):
        self._default = dict()
        self._storages = dict()

    @property
    def default(self):
        return self._default

    def get(self, name):
        return self._storages.get(name)

    def add_storage(self, name):
        self._storages[name] = dict()

    def clear(self):
        self._default.clear()
        for storage in self._storages.values():
            storage.clear()
        logger.debug('Storage cleared')


storage_manager = StorageManager()
