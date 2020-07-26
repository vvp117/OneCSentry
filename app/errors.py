from functools import wraps

from falcon import HTTPInternalServerError

from app.logs import ResourceLogger
from app.common import jdumps


class MetaError(type):

    def __init__(cls, name, bases, attrs):
        cls.__init__ = MetaError.pre_init(cls.__init__)

    @staticmethod
    def pre_init(orig_init):
        @wraps(orig_init)
        def init_wrapper(self, *args, **kwargs):

            super(type(self), self).__init__()
            orig_init(self, *args, **kwargs)

            self.headers = {'onec-sentry-error': self.__class__.__name__}

        return init_wrapper


class UnknownError(HTTPInternalServerError, metaclass=MetaError):
    def __init__(self, cause):
        self.title = 'Unknown error'
        self.description = cause


class UnderConstruction(HTTPInternalServerError, metaclass=MetaError):
    title = 'Under construction'


class HTTPErrorLogHandler(Exception):
    @staticmethod
    def handle(err, req, resp, params):
        logger = ResourceLogger()

        error_body = {
            'title': err.title,
            'description': err.description,
        }

        logger.log_resp(err, jdumps(error_body), 'onec-sentry-error')

        raise err
