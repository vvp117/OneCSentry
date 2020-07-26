from falcon import HTTPBadRequest, HTTPInternalServerError

from app.errors import MetaError


class ExecutableNotFound(HTTPBadRequest, metaclass=MetaError):
    def __init__(self, version):
        self.title = 'Executable not found'
        self.description = f'File 1cv8.exe for version {version} not found'


class FailedBatchLaunch(HTTPInternalServerError, metaclass=MetaError):
    def __init__(self, cause):
        self.title = 'Failed batch launch'
        self.description = cause
