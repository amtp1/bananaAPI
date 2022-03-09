from math import remainder
from time import sleep
from datetime import datetime as dt
from decimal import Decimal as D, ROUND_DOWN, ROUND_UP
from itertools import count

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
        self.remainder = 50 # Remainder balance. Default: roubles.
        self.percent = 0.1 # Percent value

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
        params = {
            "symbol": None,
            "side": None,
            "type": "MARKET",
            "quantity": None
        }

        count_iter: int = 0
        commission: float = 0.0
        start_time = dt.now()
        while True:
            get_price = self.get_price_by_symbol # (Function object) Gets the price of a symbol.
            get_value = self.get_value_by_symbol # (Function object) Gets the balance value of a symbol.
            to_float = self.to_float_format      # (Function object) Convert value to float type.
            percent = self.get_percent           # (Function object) Get percent.
            is_rouble_step = True # Rouble step while iterating. Default: True.
            roubles = get_value(symbol="RUB") - self.remainder # Roubles balance without remainder.
            logger.info(F"Начальный баланс: {to_float(roubles)}₽") # Show balance value with remainder.

            for step in self.steps_symbols:
                couple: list = step.get("couple") # Get couple from steps value.
                symbol: str = "".join(couple)     # Join couple in the symbol.

                params["symbol"] = symbol         # Set a symbol value in the params.
                params["side"] = step.get("side") # Set a side value in the params.

                if not couple[0] in ("USDT", "RUB",):
                    if is_rouble_step:
                        count_exchng = to_float(roubles / get_price(symbol=symbol))
                        commission+=to_float(percent((count_exchng * 0.1 / 100) * get_price("DOTUSDT"), is_dollar=True))
                        params["quantity"] = count_exchng
                        is_rouble_step=False
                        #response = self.create_new_order(**params)
                        #logger.info(F"1 ITER: {response}")
                    else:
                        remainder_usdt = get_value(symbol="USDT")
                        params["quantity"] = count_exchng
                        count_exchng = to_float(count_exchng * get_price(symbol="DOTUSDT")) + (get_value(symbol="USDT") // 1)
                        commission+=to_float(percent(count_exchng * 0.1 / 100, is_dollar=True))
                        #response = self.create_new_order(**params)
                        #logger.info(F"2 ITER: {response}")
                elif couple[0] == "USDT":
                    params["quantity"] = self.to_integer_format(count_exchng)
                    count_exchng = count_exchng * to_float(get_price(symbol=symbol))
                    commission+=to_float(percent(value=count_exchng, is_rouble=True))
                    #response = self.create_new_order(**params)
                    #logger.info(F"3 ITER: {response}")
                    is_rouble_step = True

            profit = "{:0.5f}".format(((count_exchng - commission) * 100 / roubles) - 100)
            logger.info(F"Конечный баланс: {count_exchng - commission}₽\nКомиссия: {to_float(commission)}₽\nПрофит: {profit}%\n")
            commission = 0.0

            end_time = int((dt.now() - start_time).total_seconds())

            #sleep(3)

            #if end_time >= 60:
            #    break

            count_iter+=1
            sleep(3)
            if count_iter == 5:
                break

    def to_float_format(self, price: str) -> float:
        return float("{:0.2f}".format(price))

    def to_integer_format(self, price: str) -> int:
        return int(float("{:0.2f}".format(price)))
    
    def get_percent(self, value: str = None, is_dollar: bool = False, is_rouble: bool = False) -> float:
        if is_dollar:
            value: float = value * self.get_price_by_symbol(symbol="USDTRUB")
        elif is_rouble:
            value: float = value * self.percent / 100
        return value