import os
import os.path as osp
import time
import tempfile
from multiprocessing import Event
import logging
import pytest

import logserver


@pytest.fixture
def logfile():
    filename = osp.join(tempfile.gettempdir(), "output.log")
    yield filename
    os.remove(filename)


def test_server(logfile):
    handler = logging.FileHandler(logfile)
    handler.setFormatter(logging.Formatter("%(msg)s"))
    handlers = [handler]

    done, ready = Event(), Event()

    server = logserver.make_server_process(handlers, done=done, ready=ready)
    server.start()
    ready.wait(timeout=1)

    logger = logserver.get_logger('test', stream_handler=False)

    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    logger.critical("critical")

    time.sleep(0.01)
    done.set()
    server.join(timeout=1)

    with open(logfile, "r") as lf:
        lines = [l.strip() for l in lf.readlines()]
    assert "debug" not in lines
    assert "info" in lines
    assert "warning" in lines
    assert "error" in lines
    assert "critical" in lines
