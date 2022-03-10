from pathlib import Path
from datetime import datetime as dt

import yaml
from loguru import logger

from utils.utils import *
from exceptions.exceptions import *

def main():
    if not Path(r"config.yaml").is_file():
        raise FileError("'config.yaml' is not found")

    with open(r"config.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    n_dt = dt.now().strftime("%Y-%m-%d")
    logger.add(
        r"debug/debug_%s.log" % n_dt, format="{time} {level} {message}",
        level="DEBUG", rotation="1 week",
        compression="zip")

    driver = Driver(config)
    driver.stream()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Program stopped.")