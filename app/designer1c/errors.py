from falcon import HTTPBadRequest, HTTPInternalServerError

from app.errors import OneCSentryError


class ExecutableNotFound(HTTPBadRequest, OneCSentryError):
    title = 'Executable not found'

    def __init__(self, version):
        self.prepare(
            f'File 1cv8.exe for version {version} not found')


class FailedBatchLaunch(HTTPInternalServerError, OneCSentryError):
    title = 'Failed batch launch'

    def __init__(self, cause):
        self.prepare(cause)
