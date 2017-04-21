import time
import logging
import random
from multiprocessing import Event
from logserver import LogServerProcess
from logserver.handlers import SQLiteHandler

handlers = [
    SQLiteHandler("logs.sqlite"),
    logging.StreamHandler()
]

server = LogServerProcess(handlers)
server.start()

# If we don't wait for the server to finish initializing, we can lose the first
# log message.
server.ready.wait()

logger = server.get_logger("demo")

for i in range(5):
    delay = random.randint(1, 5)
    logger.warning("Iteration %d: Sleeping for %d seconds...", i, delay)
    time.sleep(delay)
    logger.info("Iteration %d: Awoke!", i)

server.stop()
server.join()
