import typing


def get_x(spec, field, default: typing.Any = None) -> typing.Any:
    return default if spec._x is None else spec._x.get(field, default)
