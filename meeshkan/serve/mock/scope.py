class Scope:
    def __init__(self):
        self._name = None

    def set(self, name):
        self._name = name

    def get(self):
        return self._name

    def clear(self):
        self._name = None
