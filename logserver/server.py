from __future__ import print_function

import sys
import threading as th
import multiprocessing as mp
import logging
import logging.handlers
import struct
from socket import socket, AF_INET, SOCK_DGRAM
from select import select

if sys.version_info.major >= 3:
    import queue
    import pickle
else:
    import Queue as queue
    import cPickle as pickle

from . import handlers

try:
    from typing import Union
except ImportError:
    Union = None


_DEFAULT_FORMAT = "[%(levelname)1.1s %(name)s:%(lineno)d %(asctime)s] %(message)s"


class LogServer(object):
    """Base server for logging from multiple processes or threads."""
    def __init__(self, handlers=[], host=None, port=None, level=logging.INFO):
        self.host = host or "127.0.0.1"
        self.port = port or 9123

        self.handlers = handlers
        self.level = level

        # Events and queues are instantiated by implementations so we can
        # choose from either threaded or multiprocess varieties
        self.done = None   # type: Union[mp.Event, th.Event]
        self.ready = None  # type: Union[mp.Event, th.Event]

        self._record_queue = queue.Queue()  # this only runs in threads
        self._handler_queue = queue.Queue()  # type: Union[queue.Queue, mp.Queue]

        # Will be the root logger once the thread/process boots
        self.logger = None  # type: logging.Logger

        self._runtime_handlers = {}

    def add_handler(self, name, handler_class, *args, **kwargs):
        """Add a new handler to the root logger.

        .. warning::

           This will replace an existing handler of the given name. It is up to
           the main process starting a log server to keep track of named
           handlers.

        :param str name: Unique name to give the handler.
        :param str handler_class: :class:`logging.Handler` class to use; must
            be found in either :mod:`logging`, :mod:`logging.handlers`, or
            :mod:`logserver.handlers`.
        :param list args: Arguments used to instantiate the handler.
        :param dict kwargs: Keyword arguments used to instantiate the handler.
        :returns: A copy of the instantiated handler.

        """
        Handler = self.get_handler_class(handler_class)
        handler = Handler(*args, **kwargs)
        self._handler_queue.put((name, handler_class, args, kwargs))
        return handler

    def remove_handler(self, name):
        """Remove a handler from the root logger.

        :param str name: Name given to the handler.

        """
        self._handler_queue.put((name,))

    @staticmethod
    def get_handler_class(name):
        """Returns the class of a handler found in the Python standard library
        or :mod:`logserver.handlers`.

        """
        if hasattr(handlers, name):
            mod = handlers
        elif hasattr(logging, name):
            mod = logging
        elif hasattr(logging.handlers, name):
            mod = logging.handlers
        else:
            raise RuntimeError("handler class not found")

        Handler = getattr(mod, name)
        if not issubclass(Handler, logging.Handler):
            raise TypeError(name + " is not a logging.Handler")

        return Handler

    def get_logger(self, name, stream_handler=True, stream_fmt=None,
                   level=None):
        """Return a pre-configured logger that will communicate with the log
        server. If the logger already exists, it will be returned unmodified.

        :param str name: Name of the logger.
        :param bool stream_handler: Automatically add a stream handler.
        :param stream_fmt: Format to use when ``stream_handler`` is set.
        :param int level: Logging level to use.

        """
        level = level or self.level
        logger = logging.getLogger(name)
        logger.setLevel(level)

        if len(logger.handlers) > 0:
            return logger  # logger already configured

        logger.addHandler(logging.handlers.DatagramHandler(self.host, self.port))

        if stream_handler:
            if stream_fmt is None:
                stream_fmt = _DEFAULT_FORMAT
            handler = logging.StreamHandler()
            handler.setLevel(self.level)
            handler.setFormatter(logging.Formatter(stream_fmt))
            logger.addHandler(handler)

        return logger

    def _consumer_thread(self):
        """Thread for consuming log records."""
        while not self.done.is_set():
            try:
                record = self._record_queue.get(timeout=1)
                self.logger.handle(record)
            except queue.Empty:
                continue

        # Finish processing any items left in the queue before quitting
        while True:
            try:
                record = self._record_queue.get_nowait()
                self.logger.handle(record)
            except queue.Empty:
                break

    def _socket_thread(self):
        """Thread for listening on the UDP socket."""
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.bind((self.host, self.port))

        def ready():
            socks, _, _ = select([sock], [], [], 1)
            return sock in socks

        while not self.done.is_set():
            try:
                if ready():
                    data = sock.recv(4096)  # FIXME: more robust length
                    record = logging.makeLogRecord(pickle.loads(data[4:]))
                    self._record_queue.put(record)
                else:
                    continue
            except Exception as e:
                print(e)

        sock.close()

    def _handler_thread(self):
        """Thread for adding/removing handlers to the root logger."""
        while not self.done.is_set():
            try:
                msg = self._handler_queue.get(timeout=1)

                # Add a handler
                if len(msg) == 4:
                    Handler = self.get_handler_class(msg[1])
                    handler = Handler(*msg[2], **msg[3])
                    handler.setLevel(self.level)
                    # FIXME: formatter
                    # handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
                    self._runtime_handlers[msg[0]] = handler
                    self.logger.addHandler(handler)

                # Remove a handler
                elif len(msg) == 1:
                    if msg[0] in self._runtime_handlers:
                        self.logger.removeHandler(self._runtime_handlers[msg[0]])
                        self._runtime_handlers.pop(msg[0])
                    else:
                        print("Oops! No handler named", msg[0])
            except queue.Empty:
                pass
            except Exception as e:
                print(e)

    def run(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(self.level)

        if len(self.handlers) == 0:
            self.handlers.append(logging.NullHandler())

        for handler in self.handlers:
            handler.setLevel(self.level)
            self.logger.addHandler(handler)

        threads = [
            th.Thread(target=self._socket_thread),
            th.Thread(target=self._consumer_thread),
            th.Thread(target=self._handler_thread)
        ]

        [thread.start() for thread in threads]
        self.ready.set()
        [thread.join() for thread in threads]

    def stop(self):
        """Signal the server to stop."""
        self.done.set()


class LogServerProcess(LogServer, mp.Process):
    def __init__(self, handlers=[], host=None, port=None, level=logging.INFO):
        mp.Process.__init__(self)
        LogServer.__init__(self, handlers, host, port, level)

        self.done = mp.Event()
        self.ready = mp.Event()
        self._handler_queue = mp.Queue()


class LogServerThread(LogServer, th.Thread):
    def __init__(self, handlers=[], host=None, port=None, level=logging.INFO):
        th.Thread.__init__(self)
        LogServer.__init__(self, handlers, host, port, level)

        self.done = th.Event()
        self.ready = th.Event()
