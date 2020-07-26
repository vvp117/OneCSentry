from logging import getLogger
from logging.handlers import TimedRotatingFileHandler
from logging.config import dictConfig
from inspect import stack
from os import makedirs
from os.path import dirname, join
from os.path import isdir

import falcon

from app.common import yload, jdumps, Singleton


CONFIG_LOGS_FILE = 'config.logs.yaml'
LOGS_DIR = None


class ResourceLogger(metaclass=Singleton):

    @staticmethod
    def extract_headers(source, headers=''):
        if headers:
            dict_headers = {}
            for header in headers.split(','):
                name = header.strip()
                dict_headers[name] = source.headers.get(name)

            headers = f'\nheaders:\n{jdumps(dict_headers)}'

        return headers

    def __init__(self):
        self.log = getLogger('api')
        self._logger_req = getLogger('api.req')
        self._logger_resp = getLogger('api.resp')

    def log_req(self, req, body='', headers=''):
        message = f'\nbody:\n{body}' if body else ''

        query = {name: value for name, value in req.params.items()
                 if not name.endswith('pwd')}
        if query:
            query = jdumps(query)
            query = f'\nquery:\n{query}'
        else:
            query = ''

        headers = ResourceLogger.extract_headers(req, headers)

        extra_data = {
            'url': req.path,
            'template': req.uri_template,
            'resource': self.__class__.__name__,
            'method': stack()[1][3],
            'query': query,
            'headers': headers,
        }

        self._logger_req.info(message, extra=extra_data)

    def log_resp(self, resp, body='', headers=''):
        message = f'\nbody:\n{body}' if body else ''

        headers = ResourceLogger.extract_headers(resp, headers)

        extra_data = {
            'http-status': resp.status,
            'headers': headers,
        }

        if resp.status == falcon.HTTP_200:
            log_func = self._logger_resp.info

        elif resp.status >= falcon.HTTP_400:
            log_func = self._logger_resp.error

        else:
            log_func = self._logger_resp.warning

        log_func(message, extra=extra_data)


class TimedRotatingFileHandlerLogFormat(TimedRotatingFileHandler):

    def __init__(self, *args, **kwargs):

        # All logs must be in 'logs_dir'
        filename = kwargs.get('filename')
        if filename:
            kwargs['filename'] = join(LOGS_DIR, filename)

        super().__init__(*args, **kwargs)

        # Logs with '.log' suffix is beautiful
        self.suffix += '.log'


def setup_logging(logs_dir):
    global LOGS_DIR
    LOGS_DIR = logs_dir

    if logs_dir and not isdir(logs_dir):
        makedirs(logs_dir, exist_ok=True)

    config_logs = yload(join(dirname(__file__), CONFIG_LOGS_FILE))
    dictConfig(config_logs)
