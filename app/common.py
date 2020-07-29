from json import dumps as json_dumps
from hashlib import sha512
from uuid import uuid4

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


def hash_secret(secret):
    salt = uuid4().hex
    hash_res = sha512(salt.encode() + secret.encode())

    return hash_res.hexdigest() + ':' + salt


def check_secret(hashed_secret, secret_to_check):
    secret_hash, salt = hashed_secret.split(':')
    hash_res = sha512(salt.encode() + secret_to_check.encode())

    return secret_hash == hash_res.hexdigest()


class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton,
                                        cls).__call__(*args, **kwargs)
        return cls._instances[cls]
