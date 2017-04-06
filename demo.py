import time
import random
from multiprocessing import Event
import logserver
from logserver.handlers import SQLiteHandler

logger = logserver.get_logger("demo")
finished = Event()

server = logserver.make_server_process([SQLiteHandler("logs.sqlite")], done=finished)
server.start()

for _ in range(5):
    delay = random.randint(1, 5)
    logger.warning("Sleeping for %d seconds...", delay)
    time.sleep(delay)
    logger.info("Awoke!")

finished.set()
server.join()
