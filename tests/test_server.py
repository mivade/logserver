import os
import os.path as osp
import tempfile
import logging
from logging.handlers import DatagramHandler
import pytest

from logserver.server import LogServer


@pytest.fixture
def logfile():
    filename = osp.join(tempfile.gettempdir(), "output.log")
    yield filename
    os.remove(filename)


def test_server(logfile):
    handler = logging.FileHandler(logfile)
    handler.setFormatter(logging.Formatter("%(msg)s"))
    handlers = [handler]

    server = LogServer(handlers)
    server.start()

    logger = logging.getLogger("logserver")
    logger.setLevel(logging.WARNING)
    logger.addHandler(DatagramHandler(server.host, server.port))
    # logger.addHandler(DatagramHandler("127.0.0.1", 9123))

    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    logger.critical("critical")

    try:
        with open(logfile, "r") as lf:
            lines = lf.readlines()
        assert "warning" in lines
        assert "error" in lines
        assert "critical" in lines
    finally:
        # server.stop()
        server.terminate()
