


class CallbackDict:
    def __init__(self):
        self._callbacks = dict()

    def get_callback(self, host, method, path):
        return self._callbacks.get((host, method, path))

    def add_callback(self, host, method, path, callback):
        self._callbacks[(host, method, path)] = callback


callback_dict = CallbackDict()


def callback(host, method, path):
    def decorator(function):
        callback_dict.add_callback(host, method, path, function)
        return function
    return decorator





