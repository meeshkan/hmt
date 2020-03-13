import logging

logger = logging.getLogger(__name__)


class Storage:
    def __init__(self):
        self._default = dict()
        self._entities = dict()

    @property
    def default(self):
        return self._default

    def add_entity(self, name):
        self._entities[name] = list()

    def clear(self):
        self._default.clear()
        for storage in self._storages.values():
            storage.clear()
        logger.debug("Storage cleared")

    def __getattr__(self, x):
        if x in self.__dict__:
            return getattr(self, x)
        return self._entities[x]

    def __getitem__(self, x):
        return self._entities[x]


class StorageManager:
    def __init__(self):
        self._storages = dict()
        self._default = Storage()

    def add_mock(self, mockname):
        self._storages[mockname] = Storage()

    def __getitem__(self, mockname):
        return self._storages[mockname]

    @property
    def default(self):
        return self._default

    def clear(self):
        self._default.clear()
        for storage in self._storages.values():
            storage.clear()
        logger.debug("Storages cleared")


storage_manager = StorageManager()
