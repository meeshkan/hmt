

class StorageManager:
    def __init__(self):
        self._default = dict()
        self._storages = dict()

    @property
    def default(self):
        return self._default

    def get(self, name):
        return self._storages.get(name)

    def clear(self):
        self._default.clear()
        for storage in self._storages.values():
            storage.clear()


storage_manager = StorageManager()

