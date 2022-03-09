from pathlib import Path

import yaml
from loguru import logger

from utils.utils import *
from exceptions.exceptions import *

def main():
    if not Path(r"config.yaml").is_file():
        raise FileError("'config.yaml' is not found")

    with open(r"config.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    logger.add(
        r"debug/debug_check_profit.log", format="{time} {level} {message}",
        level="DEBUG", rotation="1 week",
        compression="zip")

    driver = Driver(config)
    driver.stream()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Program stopped.")