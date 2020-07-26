from falcon import HTTPBadRequest

from app.errors import MetaError


class ServerAgentServiceNotFound(HTTPBadRequest, metaclass=MetaError):
    def __init__(self):
        self.title = 'Server Agent service not found'
        self.description = '1C:Enterprise 8.3 Server Agent service not found'


class InvalidServiceStatus(HTTPBadRequest, metaclass=MetaError):
    def __init__(self, command_name, service_status):
        self.title = 'Invalid current server service status'
        self.description =\
            f'{command_name} command rejected:'\
            f'current status of service - {service_status}'


class TimeoutWaitingStopped(HTTPBadRequest, metaclass=MetaError):
    def __init__(self):
        self.title = 'Timeout waiting stopped'
