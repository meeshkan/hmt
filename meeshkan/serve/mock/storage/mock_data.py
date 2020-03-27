import typing

from meeshkan.serve.mock.storage.entity import Entity


class MockData:
    def __init__(self):
        self._default = dict()
        self._entities: typing.Dict[str, Entity] = dict()

    @property
    def default(self):
        return self._default

    def add_entity(self, entity: Entity):
        self._entities[entity.name] = entity

    def get_entity(self, name):
        return self._entities[name]

    def clear(self):
        self._default.clear()
        for entity in self._entities.values():
            entity.clear()

    def __getattr__(self, name):
        if name in self.__dict__:
            return getattr(self, name)
        return self._entities[name]

    def __getitem__(self, key):
        return self._default[key]

    def __contains__(self, key):
        return key in self._default

    def __delitem__(self, key):
        del self._default[key]

    def __setitem__(self, key, value):
        self._default[key] = value

    def get(self, key, default=None):
        return self._default.get(key, default)