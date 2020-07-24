import argparse
import shlex
from time import sleep, time
from os import listdir, path, remove

import psutil
from win32serviceutil import (
    StopService,
    StartService
)

import app.service1c.errors as errors_
import app.com1c as com1c


DEFAULT_AGENT_PORT = 1540
DEFAULT_CLUSTER_PORT = 1541
SERVICE_AGENT_EXE = r'ragent.exe'
MNGR_CLUSTER_PROC_EXE = r'rmngr.exe'
WORKING_PROC_EXE = r'rphost.exe'


parser = argparse.ArgumentParser()
parser.add_argument('exe_file')
parser.add_argument('-host')
parser.add_argument('-srvc', action='store_true')
parser.add_argument('-agent', action='store_true')
parser.add_argument('-debug', action='store_true')
parser.add_argument('-regport', type=int)
parser.add_argument('-port', type=int)
parser.add_argument('-range')
parser.add_argument('-d')


def get_args_cmdline(cmdline):

    if isinstance(cmdline, list):
        args = cmdline

    else:
        args = shlex.split(cmdline)

    known_args, _ = parser.parse_known_args(args)

    return known_args


class AgentService():

    def __init__(self, connect_params: com1c.ConnectParameters):

        self.port = int(connect_params.agent_port or DEFAULT_AGENT_PORT)
        self.regport = int(connect_params.cluster_port or DEFAULT_CLUSTER_PORT)
        self.service = None
        self.parameters = None

        self._find_agent_service()

        if not self.service:
            raise errors_.ServerAgentServiceNotFound()

    def _find_agent_service(self):

        for service in psutil.win_service_iter():
            params = service.as_dict()
            binpath = params.get('binpath', '')

            if SERVICE_AGENT_EXE not in binpath:
                continue

            parameters = get_args_cmdline(binpath)

            if parameters.port and int(parameters.port) == self.port:
                self.service = service
                self.parameters = parameters
                break

    def wait(self, expected_status, step=1, timeout=30):
        begin = time()

        while time() - begin <= timeout:
            if self.service.status() == expected_status:
                return True
            sleep(step)

        return False

    def stop(self):

        status = self.service.status()

        if status == psutil.STATUS_RUNNING:
            StopService(self.service.name())

        else:
            raise errors_.InvalidServiceStatus('Stop', status)

    def start(self):

        status = self.service.status()

        if status == psutil.STATUS_STOPPED:
            StartService(self.service.name())

        else:
            raise errors_.InvalidServiceStatus('Start', status)

    def restart(self):
        self.clear_cache()
        self.start()

    def clear_cache(self, correct_stop=True):

        status = self.service.status()

        if correct_stop:
            if status == psutil.STATUS_RUNNING:
                self.stop()
                if not self.wait(psutil.STATUS_STOPPED):
                    raise errors_.TimeoutWaitingStopped()

        # Kill processes, if exists!
        self.kill_processes(wait=True)

        # Clearing cache!
        cluster_dir = path.join(self.parameters.d, f'reg_{self.regport}')
        for elem in listdir(cluster_dir):
            if elem.startswith('snccntx'):
                cache_dir = path.join(cluster_dir, elem)
                for cachfile in listdir(cache_dir):
                    remove(path.join(cache_dir, cachfile))

    def kill_processes(self, wait=False, timeout=30):
        target_procs = [
            SERVICE_AGENT_EXE,
            MNGR_CLUSTER_PROC_EXE,
            WORKING_PROC_EXE,
        ]
        procs_to_kill = []

        for proc in psutil.process_iter():
            proc_name = proc.name()
            if proc_name not in target_procs:
                continue

            args_cmdline = get_args_cmdline(proc.cmdline())

            if proc_name == SERVICE_AGENT_EXE:
                if args_cmdline.port == self.parameters.port:
                    procs_to_kill.append(proc)

            if proc_name == MNGR_CLUSTER_PROC_EXE:
                if args_cmdline.port == self.parameters.regport:
                    procs_to_kill.append(proc)

            if proc_name == WORKING_PROC_EXE:
                if (args_cmdline.regport == self.parameters.regport
                   and args_cmdline.range == self.parameters.range):
                    procs_to_kill.append(proc)

        procs_to_kill.sort(key=lambda x: target_procs.index(x.name()))

        if wait:
            gone, procs_to_kill = psutil.wait_procs(
                procs=procs_to_kill, timeout=timeout)

        for proc in procs_to_kill:
            if proc.is_running():
                try:
                    proc.kill()
                    # TODO: Add logging!
                    print(f'Process {proc} terminated')
                except psutil.NoSuchProcess:
                    pass
                except Exception as err:
                    # TODO: Add logging!
                    print(f'Process {proc} not terminated: {err}')
