import os
import os.path as osp
import logging
from tempfile import gettempdir
import sqlite3
import pytest

from ..handlers import SQLiteHandler


@pytest.fixture
def sqlite_path():
    path = osp.join(gettempdir(), "out.sqlite")
    yield path
    os.remove(path)


def test_sqlite_handler(sqlite_path):
    handler = SQLiteHandler(sqlite_path)
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info("info")
    logger.debug("debug")
    logger.warning("warn")
    logger.error("error")
    logger.critical("critical")

    with sqlite3.connect(sqlite_path) as conn:
        res = conn.execute("SELECT levelname FROM logs").fetchall()

    levels = [level[0] for level in res]

    assert "INFO" in levels
    assert "DEBUG" not in levels
    assert "WARNING" in levels
    assert "ERROR" in levels
    assert "CRITICAL" in levels
