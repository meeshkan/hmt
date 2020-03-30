def get_x(spec, field, default=None):
    return default if spec._x is None else spec._x.get(field, default)
