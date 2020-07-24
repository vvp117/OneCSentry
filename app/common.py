from json import dumps as json_dumps

from yaml import (SafeLoader,
                  load as yaml_load,
                  dump as yaml_dump)


def yload(filename):
    with open(filename) as f:
        return yaml_load(f, Loader=SafeLoader)


def ydump(filename, data):
    with open(filename, mode='w') as f:
        yaml_dump(data, f, indent=4)


def jdumps(data):
    return json_dumps(data, ensure_ascii=False, indent=4)


class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton,
                                        cls).__call__(*args, **kwargs)
        return cls._instances[cls]
