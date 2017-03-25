import logging
from logging.handlers import NullHandler
from multiprocessing import Process, Event
from threading import Thread

try:
    from queue import Queue, Empty
    import socketserver
    import pickle
except ImportError:
    from Queue import Queue, Empty
    import cPickle as pickle


class Handler(socketserver.DatagramRequestHandler):
    def __init__(self, queue):
        self.queue = queue
        super(Handler, self).__init__()

    def handle(self):
        try:
            # It is mostly undocumented, but there are 4 bytes which give
            # the length of the pickled LogRecord.
            _ = self.rfile.read(4)
            msg = self.rfile.read()
            self.queue.put(logging.makeLogRecord(pickle.loads(msg)))
        except:
            print("Error reading log record!")


class LogServer(Process):
    """Log server process.

    :param list handlers: List of log handlers to use. If not given, only a
        :class:`logging.NullHandler` will be used.
    :param str host: Host to bind to.
    :param int port: Port number to bind to.
    :param queue: A queue to use or None to create a new one.
    :param int level: Minimum log level.

    """
    def __init__(self, handlers=[], host="127.0.0.1", port=9123, queue=None,
                 level=logging.INFO):
        self.handlers = handlers
        self.level = level

        if not self.handlers:
            self.handlers.append(NullHandler())

        self.host = host
        self.port = port
        self.queue = queue or Queue()

        self._done = Event()
        self._server = None

    def stop(self):
        """Shutdown the server."""
        self._done.set()
        self._server.shutdown()

    def consume(self):
        """Loop to consume log entries that are added to the server's queue."""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.level)

        while not self._done.is_set():
            try:
                record = self.queue.get(timeout=1)
                root_logger.handle(record)
            except Empty:
                continue

    def run(self):
        """Main target loop for the log server process. This will be started
        when calling the :meth:`start` method.

        """
        consumer = Thread(target=self.consume, name="log_consumer")
        consumer.start()

        self._server = socketserver.ThreadingUDPServer((self.host, self.port), Handler)
        self._server.serve_forever()
