from sys import argv
from os import getcwd
from os.path import abspath, dirname, splitext
import win32serviceutil
import win32service
import win32event
import servicemanager as sm
from logging import getLogger

import app
from app.config import Config, CONFIG_KEY
from app.logs import setup_logging


def handle_launch(logger_name):
    exec_file = abspath(argv[0])
    exec_dir = dirname(exec_file)
    _, exec_ext = splitext(exec_file)

    as_service = (exec_ext.lower() == '.exe')

    argv[0] = exec_file

    config = Config(exec_dir, as_service)
    config = Config()
    setup_logging(config.current['logs']['dir'])

    log = getLogger(logger_name)
    log.info('Start')
    log.info(f'exec_file={exec_file}')
    log.info(f'exec_dir={exec_dir}')
    log.info(f'getcwd()={getcwd()}')

    return as_service, log


class OneCSentryService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'OneCSentry'
    _svc_display_name_ = 'OneC: Sentry'
    _svc_description_ = '1C service and infobase management'
    _exe_args_ = None

    def __init__(self, args):
        _, self.log = handle_launch('main.service')

        self.log.info(f'Initialization: args={args}')

        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.hWaitResume = win32event.CreateEvent(None, 0, 0, None)
        self._paused = False
        self.onec_sentry = None

        self.log.info('Init successfully!')

    def SvcDoRun(self):
        self.log.info('Service start...')

        self.log_event(sm.PYS_SERVICE_STARTED)

        self.onec_sentry = app.OneCSentry()
        self.onec_sentry.watch()

    def SvcStop(self):
        self.log.info('Stopping the service...')

        self.log_event(sm.PYS_SERVICE_STOPPING)

        self.onec_sentry.free()

        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

        self.log.info('Service stopped')
        self.log_event(sm.PYS_SERVICE_STOPPED)

    def SvcPause(self):
        self.log.info('Suspending service...')

        self.ReportServiceStatus(win32service.SERVICE_PAUSE_PENDING)
        self.ReportServiceStatus(win32service.SERVICE_PAUSED)

        self.onec_sentry.free()
        self._paused = True

        self.log.info('Service has paused')
        self.log_event(sm.PYS_SERVICE_STOPPED)

    def SvcContinue(self):
        self.log.info('Continuing the service...')

        self.ReportServiceStatus(win32service.SERVICE_CONTINUE_PENDING)
        win32event.SetEvent(self.hWaitResume)

        self.ReportServiceStatus(win32service.SERVICE_RUNNING)

        self.onec_sentry.watch()
        self._paused = False

        self.log.info('Service continues to work')
        self.log_event(sm.PYS_SERVICE_STARTED)

    def log_event(self, event_id):
        sm.LogMsg(sm.EVENTLOG_INFORMATION_TYPE,
                  event_id, (self._svc_name_, ''))


if __name__ == '__main__':
    as_service, log = handle_launch('main')
    log.info(f'sys.argv={argv}')

    if len(argv) == 1:

        if as_service:
            log.info('Initialization win-service...')

            sm.Initialize()
            sm.PrepareToHostSingle(OneCSentryService)
            sm.StartServiceCtrlDispatcher()

        else:
            log.debug('Start API debug...')

            onec_sentry = app.OneCSentry()
            onec_sentry.watch()

    else:
        log.info('Command line processing...')

        if 'debug' in argv:
            config = Config()
            log.info('Add args in "argv": '
                     f'{CONFIG_KEY}, {config.file}')
            argv.append(CONFIG_KEY)
            argv.append(config.file)

        win32serviceutil.HandleCommandLine(OneCSentryService)

    log.info('Exit')
