"""Phase 1 worker placeholder. Queue processing arrives in Phase 2."""

import logging
import time

from settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.info("Worker placeholder started in %s", settings.app_env)

while True:
    time.sleep(30)
