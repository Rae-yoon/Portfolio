#!/usr/bin/python


"""log.py

Utility API for logging.

Key Features:
    - LogFormatColor: Set colors for logs.
    - UserFilter: Filter logs by current user.
    - ExactLevelFilter: Filter console logs to only a specific level while logging all levels to file.
    - QLogger: Configurable logger supporting main/worker modes and multiprocessing.
        - main: Main logger.
        - worker: Worker logger.
    - LogBus: Singleton interface to get QLogger and manage main/worker loggers.
    - multi_logger: Main and Worker loggers for multiprocessing.
        - set_multi_worker_logger: Worker logger for multiprocessing.
        - get_multi_main_logger: Main logger for multiprocessing.
    - get_env_snapshot: Capture a snapshot of the current environment.
    
Author: Raeyoon Kim
Created: 2025-08-21
"""


from __future__ import annotations
from typing import Union, Optional
import os, sys, logging, atexit
import multiprocessing as mp
from logging.handlers import TimedRotatingFileHandler, QueueHandler, QueueListener
from functools import lru_cache


class LogFormatColor(logging.Formatter):
    """Custom formatter with ANSI color support for log levels.
    
    Attributes:
        colors (dict): Colors by type.
        
        fmt (str): The log format string. Defaults to QLogger.fmt.
        datefmt (str): The date format string. Defaults to QLogger.datefmt.
    """
    
    colors = {
        'DEBUG': '\033[37m',    # gray
        'INFO': '\033[32m',     # green
        'WARNING': '\033[33m',  # yellow
        'ERROR': '\033[31m',    # red
        'CRITICAL': '\033[41m', # red-bgc
        'RESET': '\033[0m'
    }
    
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt or QLogger.fmt,
                         datefmt or QLogger.datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record with color.

        Args:
            record (logging.LogRecord): The log record.

        Returns:
            str: The colored log string.
        """
        color = self.colors.get(record.levelname, self.colors.get('RESET'))
        return f"{color}{super().format(record)}{self.colors.get('RESET')}"


class UserFilter(logging.Filter):
    """A logging filter that injects a user name into the log record.

    Args:
        name (str): The user name. Defaults to ''.
    """
    
    def __init__(self, name: str = ""):
        super().__init__()
        self.user_name = name or os.getenv("user") or ""

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter a log record by injecting the user name.

        Args:
            record (logging.LogRecord): The log record.

        Returns:
            bool: Always True.
        """
        record.user = self.user_name
        return True


class ExactLevelFilter(logging.Filter):
    """A logging filter that allows only a specific log level.

    Args:
        level (int): The log level to allow.
    """
    
    def __init__(self, level):
        super().__init__()
        self.level = level
        
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter a log record by exact level.

        Args:
            record (logging.LogRecord): The log record.

        Returns:
            bool: True if record.levelno equals self.level, else False.
        """
        return record.levelno == self.level


class QLogger:
    """A logger that supports multiprocessing and color console output.

    Attributes:
        fmt (str): Log format string.
        datefmt (str): Date format string.
        when (str): Log rotation timing.
        dir_base (str): Base directory for logs.
        count_backup (int): Number of log backups.
        console_level (int): Logging level for console.
        file_level (int): Logging level for file.
        file_format (Formatter): Formatter for file logs.
        console_format (Formatter): Formatter for console logs.
        
        name (str): Logger name. Defaults to __name__.
        mode (str): Mode, 'main' or 'worker'. Defaults to 'worker'.
        queue (Union[mp.Queue, None]): Multiprocessing queue. Defaults to None.
        utc (bool): Whether to use UTC for timestamps. Defaults to True.
        light (bool): Light mode for logger. Defaults to True.
    """
    
    fmt = "[%(asctime)s][%(process)d][%(user)s][%(pathname)s][%(levelname)s][%(funcName)s][%(lineno)d] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    when = "midnight"                  
    dir_base = os.getenv("base_logs", os.path.join(os.getenv("project","/tmp"), "project", "logs"))   
    count_backup = 14                                 
    console_level = logging.INFO              
    file_level = logging.DEBUG           
    file_format = logging.Formatter(fmt, datefmt)
    console_format = LogFormatColor(fmt, datefmt)      

    def __init__(self, name=__name__, mode='worker', queue=None, utc=True, light=True):
        self.name = name
        self.mode = mode
        self.queue = queue
        self.utc = utc
        self.light = light
        self._listener: Optional[QueueListener] = None
        self._queue: Optional[mp.Queue] = None

        self.logger = self.get_logger()
        if mode == 'main':
            self.path_log_file = self.get_path_log_file()

        if self.mode == 'main':
            self.main()
        elif self.mode == 'worker':
            self.worker()
        else:
            raise ValueError('main or worker only')

    def get_logger(self) -> logging.Logger:
        """Create a standard logger.

        Returns:
            logging.Logger: Configured logger instance.
        """
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False      
        return logger

    def get_path_log_file(self) -> str:
        """Get full path for log file.

        Returns:
            str: Log file path.
        """
        tool = os.getenv('tool_name', self.name.split('.')[0])
        user = os.getenv('user', 'unknown')
        dir = os.path.join(self.dir_base, tool, user)        
        pid = os.getenv('log_pid',None)
        if pid:
            dir = os.path.join(dir, pid)
        os.makedirs(dir, exist_ok=True)
        
        file = os.getenv('log_file', tool) + '.log'
        return os.path.join(dir, file)

    def get_console_h(self) -> logging.StreamHandler:
        """Create console handler with color and user filter.

        Returns:
            logging.StreamHandler: Configured console handler.
        """
        console_h = logging.StreamHandler(sys.stderr)
        console_h.setLevel(self.console_level)
        console_h.setFormatter(self.console_format)
        console_h.addFilter(UserFilter(os.getenv('user','unknown')))
        console_h.addFilter(ExactLevelFilter(self.console_level))
        return console_h

    def get_file_h(self) -> TimedRotatingFileHandler:
        """Create file handler with rotation.

        Returns:
            TimedRotatingFileHandler: Configured file handler.
        """
        file_h = TimedRotatingFileHandler(
            filename=self.path_log_file,
            when=self.when,
            backupCount=self.count_backup,
            encoding='utf-8',
            delay=True, 
            utc=self.utc
        )
        file_h.setLevel(self.file_level)
        file_h.setFormatter(self.file_format)
        file_h.addFilter(UserFilter(os.getenv('user')))
        return file_h
    
    def main(self):
        """Configure the logger for main mode with optional light or full queue handling.
        """
        console_h = self.get_console_h()
        file_h = self.get_file_h()
        
        if self.light:
            self._queue = None
            if not any((isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)) for h in self.logger.handlers):
                self.logger.addHandler(console_h)
            if not any(isinstance(h, TimedRotatingFileHandler) for h in self.logger.handlers):
                self.logger.addHandler(file_h)
        else:
            self._queue = mp.Queue(-1) # maxsize
            self._listener = QueueListener(self._queue, console_h, file_h, respect_handler_level=True)
            self._listener.start()
            if not any(isinstance(h, QueueHandler) for h in self.logger.handlers):
                self.logger.addHandler(QueueHandler(self._queue))

        self.logger.setLevel(self.console_level)
        atexit.register(self.close)

    def worker(self):
        """Configure the logger for worker mode using the main queue.
        """
        if self.queue is None:
            raise ValueError('worker mode needs main queue')
        self._queue = self.queue
        if not any(isinstance(h, QueueHandler) for h in self.logger.handlers):
            self.logger.addHandler(QueueHandler(self._queue))

    def _stack_level2(self, kwargs: dict) -> dict:
        """Ensure 'stacklevel' is set in logging kwargs.

        Args:
            kwargs (dict): Logging keyword arguments.

        Returns:
            dict: Updated kwargs with 'stacklevel' set to 2 if missing.
        """
        if 'stacklevel' not in kwargs:
            kwargs['stacklevel'] = 2
        return kwargs

    def debug(self, msg: str, *args, **kwargs):
        kwargs = self._stack_level2(kwargs)
        self.logger.debug(msg, *args, **kwargs)
        
    def info(self, msg: str, *args, **kwargs):     
        kwargs = self._stack_level2(kwargs)
        self.logger.info(msg, *args, **kwargs)
        
    def warning(self, msg: str, *args, **kwargs):  
        kwargs = self._stack_level2(kwargs)
        self.logger.warning(msg, *args, **kwargs)
        
    def error(self, msg: str, *args, **kwargs):    
        kwargs = self._stack_level2(kwargs)
        self.logger.error(msg, *args, **kwargs)
        
    def critical(self, msg: str, *args, **kwargs): 
        kwargs = self._stack_level2(kwargs)
        self.logger.critical(msg, *args, **kwargs)
        
    def exception(self, msg: str, *args, **kwargs):
        kwargs = self._stack_level2(kwargs)
        self.logger.exception(msg, *args, **kwargs)

    @property
    def queue_obj(self) -> Union[mp.Queue, None]:
        """Get the internal logger queue object.

        Returns:
            Union[mp.Queue, None]: Queue if exists, otherwise None.
        """
        return self._queue

    def close(self):
        """Close and cleanup all logger handlers and listener.
        """
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
            self.logger.handlers = [h for h in self.logger.handlers if not isinstance(h, QueueHandler)]
        
        try:
            
            for h in list(self.logger.handlers):
                try: h.close()
                except Exception: pass
            self.logger.handlers.clear()
        except Exception:
            pass


class LogBus:
    """Singleton bus for managing main and worker QLoggers.

    Attributes:
        _inst (Optional[LogBus]): Singleton instance.
        _main_q_logger (Optional[QLogger]): Main logger instance.
        _queue (Optional[mp.Queue]): Shared multiprocessing queue.
    """
    
    _inst: Optional['LogBus'] = None

    def __init__(self):
        self._main_q_logger: Optional[QLogger] = None
        self._queue: Optional[mp.Queue] = None

    def get_main_q_logger(self) -> Optional[QLogger]:
        """Get the main QLogger.

        Returns:
            Optional[QLogger]: The main logger if initialized.
        """
        return self._main_q_logger

    @classmethod
    def init(cls, name: str = __name__, light: bool = True, **kwargs) -> LogBus:
        """Initialize the singleton LogBus with a main logger.

        Args:
            name (str): Logger name. Defaults to __name__.
            light (bool): Whether to use light mode. Defaults to True.
            **kwargs: Additional arguments for QLogger.

        Returns:
            LogBus: The singleton instance.
        """
        if cls._inst is None:
            bus = LogBus()
            ql = QLogger(name, mode='main', light=light, **kwargs)
            bus._main_q_logger = ql
            bus._queue = ql.queue_obj
            cls._inst = bus
        return cls._inst

    @classmethod
    def bind(cls, queue: mp.Queue) -> LogBus:
        """Bind a worker to an existing queue.

        Args:
            queue (mp.Queue): Queue shared with main logger.

        Returns:
            LogBus: The singleton instance.
        """
        if cls._inst is None:            
            bus = LogBus()
            bus._queue = queue
            bus._main_q_logger = None
            cls._inst = bus
        return cls._inst

    @classmethod
    def instance(cls) -> LogBus:
        """Return the singleton instance.

        Returns:
            LogBus: The singleton instance.

        Raises:
            RuntimeError: If LogBus has not been initialized.
        """
        if cls._inst is None:
            raise RuntimeError('LogBus has not initialized yet. main calls init(), worker calls bind(queue) at first.')
        return cls._inst

    def get_worker(self, name: str) -> QLogger:
        """Get a worker QLogger for a given name.

        Args:
            name (str): Worker logger name.

        Returns:
            QLogger: Worker logger instance.
        """
        if self._queue:
            return QLogger(name, mode='worker', queue=self._queue, light=False)
        else:
            return self._main_q_logger
   
    def close(self):
        """Close main logger and clear singleton instance.
        """
        if self._main_q_logger:
            self._main_q_logger.close()
            self._main_q_logger = None
            LogBus._inst = None


def multi_logger(main_logger: QLogger, main_bus: LogBus, queue: mp.Queue, tool_name: str, times: int, module: callable, vars: dict):
    """Run a module across multiple worker processes with logging.

    Args:
        main_logger (QLogger): Main logger instance.
        main_bus (LogBus): Log bus instance.
        queue (mp.Queue): Shared queue for workers.
        tool_name (str): Base tool name.
        times (int): Number of worker processes.
        module (callable): Function to run in workers.
        vars (dict): Variables to pass to module.
    """
    if not all([main_logger, main_bus, queue]):
        main_logger, main_bus, queue = get_multi_main_logger(tool_name, light=False)
        
    main_logger.info('%s main start', tool_name)
    procs = [mp.Process(target=set_multi_worker_logger, args=(tool_name, queue, tid, module, vars)) for tid in range(0, times)]
    for p in procs: p.start()
    for p in procs: p.join()
    
    if main_bus:
        main_logger.info('%s main end', tool_name)
        main_bus.close()

def set_multi_worker_logger(tool_name: str, queue: mp.Queue, tid: int, module: callable, vars: dict):
    """Run a module function with a worker logger in a separate process.

    Args:
        tool_name (str): Base tool name.
        queue (mp.Queue): Shared logger queue.
        tid (int): Worker ID.
        module (callable): Function to run.
        vars (dict): Variables passed to module.
    """
    LogBus.bind(queue)
    worker_name = tool_name+'.worker.'+str(tid)
    worker_logger = LogBus.instance().get_worker(worker_name)
    worker_logger.info('%s start', worker_name)
    module(vars, worker_logger)
    worker_logger.info('%s end', worker_name)

def get_multi_main_logger(tool_name: str, light: bool = False) -> tuple[QLogger, LogBus, mp.Queue]:
    """Initialize or get the main logger and queue for multi-process logging.

    Args:
        tool_name (str): Tool name.
        light (bool): Whether to use light mode. Defaults to False.

    Returns:
        tuple[QLogger, LogBus, mp.Queue]: Main logger, bus, and queue.
    """
    os.environ['tool_name'] = tool_name
    main_bus = LogBus.init(name=tool_name, light=light)
    queue = LogBus.instance().queue_obj
    main_logger = LogBus.instance().get_main_q_logger()
    return main_logger, main_bus, queue

@lru_cache(maxsize=1)
def get_env_snapshot() -> dict:
    """Get a snapshot of the current environment information.

    Returns:
        dict: Dictionary containing OS, Maya, USD, Tractor, and desktop manager info.
    """    
    env_snap_shot = {}
    try:
        if os.name == 'posix':
            name = 'None'
            version = 'None'
            name_version = 'None'
            with open("/etc/os-release") as f:
                for line in f.readlines():
                    if 'pretty_name=' in line.lower():
                        name_version = line.split('=')[-1].strip('"').strip("'").strip(f'"\n')
                        break
                    elif 'name=' in line.lower():
                        name = line.split('=')[-1].strip('"').strip("'")
                    elif 'version=' in line.lower():
                        version = line.split('=')[-1].strip('"').strip("'")
            
            if not name_version:
                name_version = name + '_' + version            
            env_snap_shot['os'] = name_version
            
        elif os.name == 'nt':
            import sys
            env_snap_shot['os'] = sys.getwindowsversion()
        else:
            try:
                import platform
                osInfo = [str(platform.system()), str(platform.release()), str(platform.version())]
                env_snap_shot['os'] = ' '.join(osInfo)
            except:
                env_snap_shot['os'] = os.getenv('OS', None)
            
    except:
        env_snap_shot['os'] = None
        
    try:
        env_snap_shot['desktop manager'] = os.environ['XDG_CURRENT_DESKTOP']
    except:
        env_snap_shot['desktop manager'] = None
        
    try:
        import maya.cmds as cmds
        env_snap_shot['maya_version_cmds.about'] = cmds.about(version=True)
    except:
        try:
            env_snap_shot['maya_versions'] = [file for file in os.listdir('/usr/autodesk') if file.startswith("maya") and file.replace('maya','').isdigit()]
        except:
            try:
                env_snap_shot['maya_version_location'] = os.path.basename(os.getenv("MAYA_LOCATION", "")) or None
            except:
                env_snap_shot['maya_versions'] = None

    try:
        env_snap_shot['tractor'] = [x for x in os.listdir('/opt/pixar') if 'tractor' in x.lower()]
    except:
        env_snap_shot['tractor'] = None

    try:
        from pxr import Usd
        env_snap_shot['usd_version_Usd'] = Usd.GetVersion()  
    except:
        try:        
            from pxr import Plug
            env_snap_shot['usd_version_Plug'] = Plug.Registry().GetVersionString()             
        except:
            env_snap_shot['usd_version'] = None
            
    try:
        import pxr
        env_snap_shot['usd_package'] = pxr.__file__
    except:
        env_snap_shot['usd_package'] = None
    
            
    return env_snap_shot

