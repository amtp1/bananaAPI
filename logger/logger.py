from datetime import datetime as dt

from loguru import logger

n_dt = dt.now().strftime("%Y-%m-%d")
logger.add(
    r"debug/debug_%s.log" % n_dt, format="{time} {level} {message}",
    level="DEBUG", rotation="1 week",
    compression="zip")