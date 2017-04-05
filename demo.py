import time
import random
from logserver import LogServer, get_logger
from logserver.handlers import SQLiteHandler

logger = get_logger("demo")

server = LogServer(SQLiteHandler("logs.sqlite"))
server.start

for _ in range(10):
    delay = random.randint(1, 5)
    logger.warning("Sleeping for %d seconds...", delay)
    time.sleep(delay)
    logger.info("Awoke!")

server.stop()
