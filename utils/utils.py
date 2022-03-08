from datetime import datetime as dt
from decimal import Decimal as D, ROUND_DOWN, ROUND_UP

from binance.spot import Spot
import pandas as pd
from loguru import logger

from exceptions.exceptions import *

class Driver:
    def __init__(self, config: dict):
        self.client = Spot(key=config.get("API-Key"), secret=config.get("Secret-Key"))
        self.steps_symbols = [
            {"couple": ["DOT", "RUB"], "side": "BUY"},
            {"couple": ["DOT", "USDT"], "side": "SELL"},
            {"couple": ["USDT", "RUB"], "side": "SELL"}
        ]
        self.comission = 0.1 # Percent value

    def current_balance(self) -> float:
        balance: float = 0.0
        for coin in self.client.account().get("balances"):
            asset, free, locked = coin.values()
            if float(free) > 0:
                if not asset in ("RUB", "USDT",):
                    try:
                        price: float = float(self.depth(symbol=f"{asset}USDT", limit=1).get("bids")[0][0])
                        dollar_value: float = float(free) * price
                        balance+=dollar_value
                    except:
                        pass
                elif asset == "USDT":
                    balance+=float(free)
        return balance

    def get_value_by_symbol(self, symbol: str) -> float:
        value: float = float([coin.get("free") for coin in self.client.account().get("balances") if symbol == coin.get("asset")][0])
        return value

    def create_new_order(self, **kwargs):
        try:
            response = self.client.new_order(**kwargs)
            return response
        except Exception as e:
            raise OrderError(e)

    def depth(self, save_to_exel: bool = None, symbol: str = None, limit: int = None) -> dict:
        if not limit:
            raise DepthError("limit value is empty")
        elif not symbol:
            raise DepthError("symbol value is empty")

        try:
            last_orders = self.client.depth(symbol=symbol, limit=limit)
            if save_to_exel:
                df = pd.DataFrame(last_orders)
                df.to_excel("orders.xlsx")
            return last_orders
        except Exception as e:
            raise DepthError(e)

    def my_trades(self, symbol: str = None):
        # time = dt.fromtimestamp(int(str(trade["time"])[:-3])).strftime("%Y-%m-%d %H:%M:%S")
        try:
            trades = self.client.my_trades(symbol=symbol)
            return trades
        except Exception as e:
            raise TradesError(e)

    def exchange_info(self, symbol: str = None):
        if not symbol:
            raise ExchangeError("symbol value is empty")

        exchng_info = self.client.exchange_info(symbol=symbol)
        return exchng_info

    def trade_fee(self, symbol: str = None):
        if not symbol:
            raise TradesError("symbol value is empty")

        fee = self.client.trade_fee(symbol=symbol)
        return fee

    def get_price_by_symbol(self, symbol: str = None, limit: int = 3) -> float:
        value: float = 0.0
        bids = self.depth(symbol=symbol, limit=limit).get("bids")
        for n in bids:
            value+=float(n[0])
        return float("{:0.2f}".format(value/limit))

    def stream(self):
        #print(self.current_balance())
        params = {
            "symbol": None,
            "side": None,
            "type": "MARKET",
            "quantity": None
        }

        count_iter: int = 0
        while True:
            get_price = self.get_price_by_symbol
            get_value = self.get_value_by_symbol
            is_rouble_step = True
            roubles = get_value(symbol="RUB") - 100
            logger.info(F"Начальный баланс(RUB): {roubles + 100}")
            """
            for coin in self.steps_symbols:
                couple: list = coin.get("couple")
                if not couple[0] in ("USDT", "RUB",):
                    symbol = "".join(couple)
                    params["symbol"] = symbol
                    params["side"] = coin.get("side")
                    if is_rouble_step:
                        first_count_coins = roubles / get_price(symbol=symbol) # For our example is DOT.
                        is_rouble_step = False
                        params["quantity"] = float("{:0.2f}".format(first_count_coins))
                        print(first_count_coins)
                        response = self.create_new_order(**params)
                        logger.info(F"1 Order => {response}")
                    else:
                        params["symbol"] = symbol
                        params["side"] = coin.get("side")
                        second_count_coins = first_count_coins * get_price(symbol=symbol) + (get_value(symbol="USDT") // 1) # For our example is USDT.
                        params["quantity"] = float("{:0.2f}".format(first_count_coins))
                        print(second_count_coins)
                        response = self.create_new_order(**params)
                        logger.info(F"2 Order => {response}")
                elif couple[0] == "USDT":
                    symbol = "".join(couple)
                    params["symbol"] = symbol
                    params["side"] = coin.get("side")
                    third_count_coins = second_count_coins * get_price(symbol=symbol)
                    params["quantity"] = int(float("{:.2f}".format(second_count_coins)))
                    response = self.create_new_order(**params)
                    logger.info(F"3 Order => {response}")
                    is_rouble_step = True
            

            logger.info(F"Конечный баланс(RUB): {third_count_coins}")
            percent = third_count_coins * 100 / roubles
            logger.info(F"Профит: {percent - 100.0 - 0.4}%\n")
            """
            count_iter+=1

            if count_iter == 1:
                break