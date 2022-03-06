from datetime import datetime as dt

from types import NoneType
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

    def depth(self, save_to_exel: NoneType = None, symbol: str = None, limit: int = None) -> dict:
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
        exchng_info = self.client.exchange_info(symbol=symbol)
        return exchng_info

    def trade_fee(self, symbol: str = None):
        fee = self.client.trade_fee(symbol=symbol)
        return fee

    def get_price_by_symbol(self, symbol: str = None) -> float:
        return self.depth(symbol=symbol, limit=1).get("bids")[0][0]

    def stream(self):
        #print(self.current_balance())
        params = {
            "symbol": None,
            "side": None,
            "type": "MARKET",
            "quantity": None
        }

        step_count: int = 0
        for coin in self.steps_symbols:
            couple: list = coin.get("couple")
            get_price = self.get_price_by_symbol
            if not couple[0] in ("USDT", "RUB",):
                #print(self.get_value_by_symbol(symbol=couple[1]))
                symbol = "".join(couple)
                params["symbol"] = symbol
                params["side"] = coin.get("side")
            elif couple[0] == "USDT":
                symbol = "".join(couple)
            print(get_price(symbol=symbol))
            #step_count+=1
            #if step_count == 3:
            #    break