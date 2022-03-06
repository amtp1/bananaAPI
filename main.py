from pathlib import Path
from datetime import datetime as dt

import pandas as pd
from binance.spot import Spot
import yaml

from loguru import logger
from time import sleep

from utils.utils import *
from exceptions.exceptions import *

BASE_DIR = Path(__file__).resolve().parent

def main():
    if not Path(r"%s\\config.yaml" % BASE_DIR).is_file():
        raise FileError("'config.yaml' is not found")

    with open(r"config.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    logger.add(
        r"debug/debug.log", format="{time} {level} {message}",
        level="DEBUG", rotation="1 week",
        compression="zip")

    driver = Driver(config)

    params = {
        'symbol': 'USDTRUB',
        'side': "BUY",
        'type': 'MARKET',
        'quantity': 25,
    }

    driver.stream()

    #response = driver.create_new_order(**params)
    #print(response)

    """
    with open(f"orders_100.txt", "w") as f:
        for i in range(0, 100):
            if i % 2 == 0:
                params["side"] = "SELL"
            else:
                params["side"] = "BUY"
            response = driver.create_new_order(**params)
            f.write(str(response)+"\n")
        f.close()
    """

    #print(driver.depth(symbol="DOTRUB", limit=5))
    #print(driver.my_trades(symbol="DOTUSDT"))
    #fee = driver.trade_fee(symbol="DOTUSDT")
    #print(fee)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Program stopped.")