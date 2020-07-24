from json import loads
from tempfile import NamedTemporaryFile
from os import remove

import falcon
import pythoncom

import app.errors as errors_
import app.service1c as svc1c
import app.com1c as com1c
import app.designer1c as designer1c
from app.logs import ResourceLogger
from app.common import jdumps
from app.config import Config


pythoncom.CoInitialize()


class AuthMiddleware(object):

    def process_request(self, req, resp):
        api_key = req.get_header('api-key')

        config = Config()
        if api_key != config.current['api-key']:
            raise falcon.HTTPUnauthorized(
                title='"API-key" required',
                description='Please provide api-key in headers')


class IndexResource(ResourceLogger):

    def on_get(self, req, resp):
        self.log_req(req)
        self.log.info('Test API')

        resp.status = falcon.HTTP_200
        resp.body = jdumps(
            {'status': 'Your boat is ready captain!'}
        )

        self.log_resp(resp, resp.body)


def get_agent(req):
    connect_params = com1c.ConnectParameters(**req.params)
    return com1c.Agent(connect_params)


def get_agent_service(req):
    connect_params = com1c.ConnectParameters(**req.params)
    return svc1c.AgentService(connect_params)


class AgentServiceResource(ResourceLogger):

    def on_get(self, req, resp):
        self.log_req(req)

        agent_service = get_agent_service(req)

        info = agent_service.service.as_dict()
        info.update({'parameters': agent_service.parameters.__dict__})

        resp.body = jdumps(info)

        self.log_resp(resp, resp.body)

    def on_post(self, req, resp, action):
        self.log_req(req)

        action_mapping = {
            'start': svc1c.AgentService.start,
            'stop': svc1c.AgentService.stop,
            'restart': svc1c.AgentService.restart,
            'clear_cache': svc1c.AgentService.clear_cache,
            'kill_processes': svc1c.AgentService.kill_processes,
        }

        if action not in action_mapping:
            # TODO: Add special error!
            raise errors_.UnknownError('Unknown command: {action}')

        agent_service = get_agent_service(req)

        action_method = action_mapping.get(action)
        getattr(agent_service, action_method.__name__)()

        resp.body = jdumps({'result': 'in progress'})

        self.log_resp(resp, resp.body)


class InfobaseResource(ResourceLogger):

    def on_get_sessions(self, req, resp, name):
        self.log_req(req)

        agent = get_agent(req)

        sessions = []
        for session in com1c.InfoBase(agent, name).sessions():
            sessions.append(
                {
                    'UserName': session.userName,
                    'SessionID': session.SessionID,
                    'AppID': session.AppID,
                    'Host': session.Host,
                    'StartedAt': session.StartedAt.isoformat(),
                }
            )

        resp.body = jdumps(sessions)

        self.log_resp(resp, f'Found {len(sessions)} sessions')

    def on_get_connections(self, req, resp, name):
        self.log_req(req)

        agent = get_agent(req)

        connections = []
        for connect in com1c.InfoBase(agent, name).connections(short=False):
            connections.append(
                {
                    'UserName': connect.userName,
                    'ConnID': connect.ConnID,
                    'AppID': connect.AppID,
                    'HostName': connect.HostName,
                    'ConnectedAt': connect.ConnectedAt.isoformat(),
                }
            )

        resp.body = jdumps(connections)

        self.log_resp(resp, f'Found {len(connections)} connections')

    def on_get(self, req, resp, name):
        self.log_req(req)

        agent = get_agent(req)
        infobase = com1c.InfoBase(agent, name)

        resp.body = jdumps(infobase.get_props())
        resp.status = falcon.HTTP_200

        self.log_resp(resp, resp.body)

    def on_post(self, req, resp, name):
        try:
            str_props = req.bounded_stream.read().decode()
            new_props = loads(str_props)
        except Exception as err:
            # TODO: Add special error!
            raise errors_.UnknownError(str(err))

        self.log_req(req, jdumps(new_props))

        agent = get_agent(req)
        infobase = com1c.InfoBase(agent, name)

        new_props = loads(req.bounded_stream.read().decode())
        result_set = infobase.set_props(new_props)

        resp.body = jdumps(result_set)

        self.log_resp(resp, resp.body)

    def on_put_cf_file(self, req, resp, name):
        cf_bytes = req.bounded_stream.read()
        if not cf_bytes:
            # TODO: Add special error!
            self.log_req(req, 'Empty!')
            raise errors_.UnknownError('No CF-file in body')

        self.log_req(req, f'File size {len(cf_bytes)} bytes')

        agent = get_agent(req)
        infobase = com1c.InfoBase(agent, name)
        infobase.close_designer()

        cf_file = NamedTemporaryFile(
            suffix=f'{name}_update.cf',
            delete=False)
        cf_file.write(cf_bytes)
        cf_file.close()

        designer = designer1c.Designer(infobase)
        code, message = designer.load_cf(cf_file.name)

        remove(cf_file.name)

        resp.body = jdumps({'code': code, 'message': message})

        self.log_resp(resp, resp.body)

    def on_put_cfdb_update(self, req, resp, name):
        self.log_req(req)

        agent = get_agent(req)
        infobase = com1c.InfoBase(agent, name)
        infobase.close_designer()

        designer = designer1c.Designer(infobase)
        code, message = designer.update_dbcf()

        resp.body = jdumps({'code': code, 'message': message})
