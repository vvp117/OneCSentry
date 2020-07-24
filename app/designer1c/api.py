from subprocess import check_call, PIPE, DEVNULL
from tempfile import NamedTemporaryFile
from os import remove, environ, path

import app.designer1c.errors as errors_
import app.service1c as svc1c
import app.com1c as com1c


class Designer(object):

    def __init__(self, infobase: com1c.InfoBase):
        self.ib = infobase
        self.usr = infobase.agent.params.usr
        self.pwd = infobase.agent.params.pwd
        self.access_code = infobase.get_props().get('PermissionCode', '')

        agent_service = svc1c.AgentService(infobase.agent.params)
        path_parts = agent_service.parameters.exe_file.split('\\')
        self.version = path_parts[-3]

        self.exe_file = self.exe_file()

    def exe_file(self):
        program_files_envs = [
            'programfiles(x86)',
            'programfiles',
            'ProgramW6432',
        ]

        for env_var in program_files_envs:
            if env_var not in environ:
                continue

            exe_file = path.join(environ[env_var],
                                 '1cv8',
                                 self.version,
                                 'bin',
                                 '1cv8.exe')
            if path.isfile(exe_file):
                return exe_file

        raise errors_.ExecutableNotFound(self.version)

    def cmd_args(self, *args):
        cmd_args = [
            self.exe_file,
            'designer',
            r'/S',
            f'{self.ib.server}\\{self.ib.name}',
            r'/WA-',
            r'/DisableStartupDialogs',
            r'/DisableStartupMessages',
            r'/UC',
            self.access_code
        ]

        if self.usr:
            cmd_args.extend([r'/n', self.usr])

        if self.pwd:
            cmd_args.extend([r'/p', self.pwd])

        cmd_args.extend(args)

        return cmd_args

    def run(self, *args, timeout=60):
        cmd_args = self.cmd_args(*args)

        log = NamedTemporaryFile(
            suffix=f'{self.ib.name}_update.log',
            delete=False)
        log.close()
        cmd_args.extend([r'/Out', log.name])

        try:
            code = check_call(
                cmd_args,
                stdout=PIPE,
                stderr=PIPE,
                stdin=DEVNULL,
                shell=True,
                text=True,
                timeout=timeout,
                encoding='cp866')

        except Exception as err:
            code = 117
            raise errors_.FailedBatchLaunch(str(err))

        else:
            with open(log.name, 'r') as log:
                message = log.read()
            remove(log.name)

        return code, message

    def load_cf(self, file_path):
        return self.run(r'/LoadCfg',
                        file_path,
                        timeout=self.ib.agent.params.timeout)

    def update_dbcf(self):
        return self.run(r'/UpdateDBCfg',
                        timeout=self.ib.agent.params.timeout)
