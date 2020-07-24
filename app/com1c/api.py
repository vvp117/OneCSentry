import win32com.client as com
from pywintypes import TimeType
import pythoncom

import app.service1c as svc1c
import app.com1c.errors as errors_


def pywintime_to_iso(date):
    return date.isoformat()


def pywintime_from_iso(date):
    if date:
        return TimeType.fromisoformat(date)
    else:
        # Empty date for 1C
        return TimeType.fromisoformat('0100-01-01T00:00:00+00:00')


def get_connector(version):
    try:
        pythoncom.CoInitialize()
        return com.Dispatch(f'V{version}.COMConnector')
    except Exception as err:
        raise errors_.UnableCreateConnector(str(err))


class ConnectParameters():

    def __init__(self, **params):
        self.version = params.get('version', '83')

        self.host = params.get('host', 'localhost')
        self.timeout = int(params.get('timeout', 60))

        self.agent_port = int(params.get('agent_port',
                              svc1c.DEFAULT_AGENT_PORT))
        self.cluster_port = int(params.get('cluster_port',
                                svc1c.DEFAULT_CLUSTER_PORT))

        self.usr = params.get('usr', '')
        self.pwd = params.get('pwd', '')
        self.access_code = params.get('access_code', '')

        self.server_admin = params.get('server_admin', '')
        self.server_pwd = params.get('server_pwd', '')

        self.cluster_admin = params.get('cluster_admin', '')
        self.cluster_pwd = params.get('cluster_pwd', '')


class Agent:

    def __init__(self, params: ConnectParameters):
        self.connector = get_connector(params.version)
        self.params = params

        try:
            self.connection = self.connector.ConnectAgent(
                f'tcp://{self.params.host}:{self.params.agent_port}'
            )
        except Exception as err:
            raise errors_.NotConnectAgent(str(err))

        self.connection.AuthenticateAgent(self.params.server_admin,
                                          self.params.server_pwd)

        self.cluster = None
        for cluster in self.connection.GetClusters():
            if cluster.MainPort == self.params.cluster_port:
                self.cluster = cluster
                break

        if self.cluster:
            self.connection.Authenticate(self.cluster,
                                         self.params.cluster_admin,
                                         self.params.cluster_pwd)
        else:
            raise errors_.ClusterNotDefined(cluster_port=self.regport)

    def infobases(self):
        return self.connection.GetInfoBases(self.cluster)

    def work_processes(self):
        work_procs = []

        all_work_procs = self.connection.GetWorkingProcesses(self.cluster)
        for work_proc in all_work_procs:
            if (work_proc.Running == 1
               and work_proc.IsEnable
               and work_proc.Use == 1):
                work_procs.append(work_proc)

        # TODO: Use exception when getting!
        # if not work_procs:
        #     errors.WorkProcessesNotFound(cluster_port=cluster_port)
        return work_procs


class InfoBase:

    allow_read_props = {
        'Name': None,
        'dbName': None,
        'dbServerName': None,
        'ScheduledJobsDenied': None,
        'SessionsDenied': None,
        'PermissionCode': None,
        'DeniedFrom': pywintime_to_iso,
        'DeniedTo': pywintime_to_iso,
        'DeniedMessage': None,
    }

    allow_write_props = {
        'ScheduledJobsDenied': None,
        'SessionsDenied': None,
        'PermissionCode': None,
        'DeniedFrom': pywintime_from_iso,
        'DeniedTo': pywintime_from_iso,
        'DeniedMessage': None,
    }

    def __init__(self, agent: Agent, name):
        self.server = agent.params.host
        self.name = name
        self.agent = agent

        self.ib = None
        self.work_proc = None

        for ib in agent.infobases():
            if str(ib.Name).upper() == name.upper():
                self.ib = ib
                break
        if not self.ib:
            raise errors_.InfobaseNotFound(name)

    def read(self):
        for work_proc_info in self.agent.work_processes():
            work_proc = WorkingProcess(self.agent, work_proc_info)

            ib = work_proc.get_infobase(self.ib.Name)
            if ib:
                self.ib = ib
                self.work_proc = work_proc
                return True

        raise errors_.InfobaseNotRead(self.name)

    def get_props(self):
        if not self.work_proc:
            self.read()

        info = {}
        for prop, converter in InfoBase.allow_read_props.items():
            value = getattr(self.ib, prop)
            if converter:
                value = converter(value)
            info.setdefault(prop, value)

        return info

    def set_props(self, new_props):
        if not self.work_proc:
            self.read()

        set_props = []
        missed_props = []
        unchanged = []
        for prop, value in new_props.items():
            if prop not in InfoBase.allow_write_props:
                missed_props.append(prop)
                continue

            converter = InfoBase.allow_write_props.get(prop)
            if converter:
                value = converter(value)

            if getattr(self.ib, prop) == value:
                unchanged.append(prop)

            else:
                setattr(self.ib, prop, value)
                set_props.append(prop)

        if set_props:
            self.update()

        return {
            'set': set_props,
            'unchanged': unchanged,
            'missed': missed_props
            }

    def sessions(self):
        return self.agent.connection.GetInfoBaseSessions(
            self.agent.cluster,
            self.ib)

    def connections(self, short=True):
        if short:
            return self.agent.connection.GetInfoBaseConnections(
                self.agent.cluster,
                self.ib)

        if not self.work_proc:
            self.read()

        return self.work_proc.connection.GetInfoBaseConnections(self.ib)

    def update(self):
        self.work_proc.connection.UpdateInfoBase(self.ib)

    def close_designer(self):
        for session in self.sessions():
            if session.AppID.upper() == 'DESIGNER':
                self.agent.connection.TerminateSession(
                    self.agent.cluster,
                    session)


class WorkingProcess:

    def __init__(self, agent, work_proc_info):
        self.connection = agent.connector.ConnectWorkingProcess(
            f'tcp://{work_proc_info.HostName}:{work_proc_info.MainPort}'
        )

        self.connection.AuthenticateAdmin(agent.params.cluster_admin,
                                          agent.params.cluster_pwd)
        self.connection.AddAuthentication(agent.params.usr,
                                          agent.params.pwd)

    def get_infobase(self, name):
        for ib in self.connection.GetInfoBases():
            if ib.Name == name:
                return ib
