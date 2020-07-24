from os.path import dirname, abspath, join
from os.path import isfile
from sys import argv
from copy import deepcopy
from uuid import uuid4

from app.common import yload, ydump, Singleton


CONFIG_KEY = '--config'
CONFIG_FILE = 'config.yaml'


class Config(metaclass=Singleton):

    def __init__(self, exec_dir, is_exe_file):
        self.default = yload(join(dirname(__file__), CONFIG_FILE))
        self.current = deepcopy(self.default)

        if CONFIG_KEY in argv:
            self.file = abspath(argv[argv.index(CONFIG_KEY)+1])

        elif is_exe_file:
            self.file = join(exec_dir, CONFIG_FILE)

        else:
            self.file = abspath(join(dirname(exec_dir), CONFIG_FILE))

        if not isfile(self.file):
            self.init_config_file()

        self.read()

    def init_config_file(self):
        init_cfg = deepcopy(self.default)
        init_cfg['api-key'] = str(uuid4())
        init_cfg['logs']['dir'] = join(dirname(self.file), 'logs')

        ydump(self.file, init_cfg)

    def read(self):
        read_cfg = yload(self.file)
        self.current.update(read_cfg)
