from falcon import HTTPInternalServerError, HTTPBadRequest

from app.errors import MetaError


class UnableCreateConnector(HTTPInternalServerError, metaclass=MetaError):
    def __init__(self, cause):
        self.title = 'Unable to create connector'
        self.description = cause


class NotConnectAgent(HTTPInternalServerError, metaclass=MetaError):
    def __init__(self, cause):
        self.title = 'Failed to connect to agent'
        self.description = cause


class ClusterNotDefined(HTTPBadRequest, metaclass=MetaError):
    def __init__(self, cluster_port):
        self.title = 'Cluster is not defined'
        self.description = f'Cluster not found on port "{cluster_port}"'


class InfobaseNotFound(HTTPBadRequest, metaclass=MetaError):
    def __init__(self, ib_name):
        self.title = 'Infobase not found'
        self.description = f'Infobase "{ib_name}" not found'


class InfobaseNotRead(HTTPBadRequest, metaclass=MetaError):
    def __init__(self, ib_name):
        self.title = 'Infobase not read'
        self.description = f'Infobase "{ib_name}" not read'


class WorkProcessesNotFound(HTTPBadRequest, metaclass=MetaError):
    def __init__(self, cluster_port):
        self.title = 'No active work processes'
        self.description =\
            f'No active work processes found on cluster "{cluster_port}"'
