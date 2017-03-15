import logging
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
        self.table_name = table_name

        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS logs ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "name TEXT,"
                "levelname TEXT,"
                "timestamp REAL,"
                "pathname TEXT,"
                "lineno INTEGER,"
                "threadName TEXT,"
                "processName TEXT,"
                "msg TEXT )")

            conn.execute("CREATE INDEX IF NOT EXISTS ix_logs_name ON logs (name)")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_logs_levelname ON logs (levelname)")

            if use_wal:
                conn.execute("PRAGMA journal_mode = wal")

    def emit(self, record):
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO logs"
                "(name, levelname, timestamp, pathname, lineno, threadName,"
                " processName, msg) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (record.name, record.levelname, record.created,
                 record.pathname, record.lineno, record.threadName,
                 record.processName, record.msg))


if __name__ == "__main__":
    logger = logging.getLogger("test")
    logger.setLevel(level=logging.INFO)
    logger.addHandler(SQLiteHandler("/tmp/test3.sqlite"))

    logger.debug("I shouldn't be logged because I'm a debug message")
    logger.info("this is a log message with info level")
    logger.error("this is a log message with error level")
    logger.warning("just a warning")
    logger.critical("STOP EVERYTHING!")
