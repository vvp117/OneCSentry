from falcon import HTTPInternalServerError

from app.logs import ResourceLogger
from app.common import jdumps


class OneCSentryError(ResourceLogger):

    def prepare(self, description=None):
        super(type(self), self).__init__()
        super().__init__()

        error_title = getattr(self.__class__, 'title', '')
        if error_title:
            self.title = error_title

        if description:
            self.description = description

        self.headers = {'onec-sentry-error': self.__class__.__name__}

        error_body = {
            'title': error_title,
            'description': description,
        }
        error_body = jdumps(error_body)
        self.log_resp(self, error_body, 'onec-sentry-error')


class UnknownError(HTTPInternalServerError, OneCSentryError):
    title = 'Unknown error'

    def __init__(self, cause):
        self.prepare(cause)


class UnderConstruction(HTTPInternalServerError, OneCSentryError):
    title = 'Under construction'

    def __init__(self):
        self.prepare()
