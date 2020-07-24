from falcon import HTTPInternalServerError, HTTPBadRequest

from app.errors import OneCSentryError


class UnableCreateConnector(HTTPInternalServerError, OneCSentryError):
    title = 'Unable to create connector'

    def __init__(self, cause):
        self.prepare(cause)


class NotConnectAgent(HTTPInternalServerError, OneCSentryError):
    title = 'Failed to connect to agent'

    def __init__(self, cause):
        self.prepare(cause)


class ClusterNotDefined(HTTPBadRequest, OneCSentryError):
    title = 'Cluster is not defined'

    def __init__(self, cluster_port):
        self.prepare(
            f'Cluster not found on port "{cluster_port}"')


class InfobaseNotFound(HTTPBadRequest, OneCSentryError):
    title = 'Infobase not found'

    def __init__(self, ib_name):
        self.prepare(
            f'Infobase "{ib_name}" not found')


class InfobaseNotRead(HTTPBadRequest, OneCSentryError):
    title = 'Infobase not read'

    def __init__(self, ib_name):
        self.prepare(
            f'Infobase "{ib_name}" not read')


class WorkProcessesNotFound(HTTPBadRequest, OneCSentryError):
    title = 'No active work processes'

    def __init__(self, cluster_port):
        self.prepare(
            f'No active work processes found on cluster "{cluster_port}"')
