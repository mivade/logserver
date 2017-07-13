import logging
import traceback as tb
import sqlite3


class SQLiteHandler(logging.Handler):
    """Handler to write logs to a SQLite database.

    :param str path: Path to SQLite file.
    :param str table_name: Name of the table to write logs to.
    :param bool use_wal: Enable the WAL journal mode. This generally improves
        performance.
    :param int level: Minimum logging level.

    """
    def __init__(self, path, table_name="logs", use_wal=True,
                 level=logging.INFO):
        super(SQLiteHandler, self).__init__(level)

        self.path = path

        for char in table_name:
            if not char.isalnum():
                raise RuntimeError("Invalid table name: " + table_name)
        self.table = table_name

        with sqlite3.connect(self.path) as conn:
            query = [
                "CREATE TABLE IF NOT EXISTS {:s} ( ".format(self.table),
                "id INTEGER PRIMARY KEY AUTOINCREMENT, ",
                "name TEXT, levelno INTEGER, levelname TEXT, timestamp REAL, ",
                "pathname TEXT, lineno INTEGER, threadName TEXT, ",
                "processName TEXT, msg TEXT, exc_info TEXT )"
            ]
            conn.execute(''.join(query))

            query = "CREATE INDEX IF NOT EXISTS ix_logs_{col:s} ON {table:s} ({col:s})"
            conn.execute(query.format(col="name", table=self.table))
            conn.execute(query.format(col="levelname", table=self.table))
            conn.execute(query.format(col="levelno", table=self.table))

            conn.isolation_level = None  # workaround for Python 3.6
            if use_wal:
                conn.execute("PRAGMA journal_mode = wal")
            conn.isolation_level = ""  # new default; not strictly necessary here

    def emit(self, record):
        with sqlite3.connect(self.path) as conn:
            query = [
                "INSERT INTO {:s}".format(self.table),
                "(name, levelno, levelname, timestamp, pathname, lineno, threadName,",
                " processName, msg, exc_info) ",
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            ]

            if record.exc_info is not None:
                exc = '\n'.join(tb.format_exception(*record.exc_info))
            else:
                exc = None

            conn.execute("".join(query),
                         (record.name, record.levelno, record.levelname,
                          record.created, record.pathname, record.lineno,
                          record.threadName, record.processName, record.msg,
                          exc))
