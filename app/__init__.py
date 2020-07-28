from wsgiref import simple_server
from logging import getLogger

from falcon import API
from falcon.http_error import HTTPError

from app import view
from app.config import Config
from app.errors import HTTPErrorLogHandler


class OneCSentry():

    def __init__(self):
        self.log = getLogger('main.app')
        self.log.info('Initialization...')

        self.api = API(
            middleware=[
                view.AuthMiddleware(),
                view.BodyTranslator(),
                ]
        )

        self.api.add_error_handler(HTTPError, HTTPErrorLogHandler.handle)

        self.set_routes()

        host = '127.0.0.1'
        port = Config().current['port']
        self.httpd = simple_server.make_server(host, port, self.api)

        self.log.info(f'Make server, port={port}')

    def watch(self):
        self.log.info('Watch...')

        self.httpd.serve_forever()

    def free(self):
        self.log.info('Shutdown...')

        self.httpd.shutdown()
        self.httpd.server_close()

        self.log.info('HTTPD shutdown, server close')

    def set_routes(self):

        # GET: test index
        self.api.add_route('/index',
                           view.IndexResource())

        infobase = view.InfobaseResource()
        # GET: all sessions
        self.api.add_route('/infobase/{name}/sessions',
                           infobase, suffix='sessions')
        # GET: all connections
        self.api.add_route('/infobase/{name}/connections',
                           infobase, suffix='connections')
        # GET: all settings
        self.api.add_route('/infobase/{name}',
                           infobase)
        # POST: set new settings infobase
        self.api.add_route('/infobase/{name}',
                           infobase)
        # PUT: load new cf-file
        self.api.add_route('/infobase/{name}/cf/file',
                           infobase, suffix='cf_file')
        # PUT: update database configuration
        self.api.add_route('/infobase/{name}/cfdb/update',
                           infobase, suffix='cfdb_update')

        agent_service = view.AgentServiceResource()
        # GET: info
        self.api.add_route('/service/info',
                           agent_service)
        # POST: start/stop/restart
        self.api.add_route('/service/{action}',
                           agent_service)
