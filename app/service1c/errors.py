from falcon import HTTPBadRequest

from app.errors import OneCSentryError


class ServerAgentServiceNotFound(HTTPBadRequest, OneCSentryError):
    title = 'Server Agent service not found'

    def __init__(self):
        self.prepare(
            '1C:Enterprise 8.3 Server Agent service not found')


class InvalidServiceStatus(HTTPBadRequest, OneCSentryError):
    title = 'Invalid current server service status'

    def __init__(self, command_name, service_status):
        self.prepare(
            f'{command_name} command rejected:'
            f'current status of service - {service_status}')


class TimeoutWaitingStopped(HTTPBadRequest, OneCSentryError):
    title = 'Timeout waiting stopped'

    def __init__(self):
        self.prepare()
