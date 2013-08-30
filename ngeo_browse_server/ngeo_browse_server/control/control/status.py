from os.path import exists
from ConfigParser import ConfigParser
from functools import wraps

from ngeo_browse_server.config import get_ngeo_config
from ngeo_browse_server.lock import FileLock
from ngeo_browse_server.control.control.config import (
    get_status_config_path, get_status_config_lockfile_path, 
    create_status_config, STATUS_SECTION
)


def get_status(config=None):
    """ Convenience function to return a `Status` object with the global 
        configuration. 
    """

    config = config or get_ngeo_config()
    return Status(config)


def locked(timeout=None):
    """ Decorator for methods that shall lock the status configuration.
    """
    
    def wrap_fn(fn):
        @wraps(fn)
        def wrap_call(*args, **kwargs):
            config = get_ngeo_config()
            lockfile = get_status_config_lockfile_path()
            with FileLock(lockfile, timeout):
                return fn(*args, **kwargs)
        #return LockGuard(fn, timeout)
        return wrap_call
    return wrap_fn


class Status(object):

    commands = frozenset(("pause", "resume", "start", "shutdown", "restart"))

    def __init__(self, config=None):
        self.config = config or get_ngeo_config()


    def _status_config(self):
        status_config_path = get_status_config_path(self.config)
        if not exists(status_config_path):
            create_status_config(status_config_path)

        parser = ConfigParser()
        with open(status_config_path) as f:
            parser.readfp(f)
        return parser

    def command(self, command):
        command = command.lower()

        if command in self.commands:
            return getattr(self, command)()

        raise AttributeError

    @locked()
    def pause(self):
        raise NotImplemented

    @locked()
    def resume(self):
        raise NotImplemented

    @locked()
    def start(self):
        raise NotImplemented

    @locked()
    def shutdown(self):
        raise NotImplemented

    @locked()
    def restart(self):
        raise NotImplemented

    @locked(timeout=1.)
    def state(self):
        status_config = self._status_config()
        return status_config.get(STATUS_SECTION, "state")

    def __str__(self):
        return self.state()