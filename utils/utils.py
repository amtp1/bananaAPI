from math import remainder
from time import sleep
from datetime import datetime as dt
from itertools import count

from binance.spot import Spot
import pandas as pd
from loguru import logger

from .formatting import *
from exceptions.exceptions import *


class Driver:
    def __init__(self, config: dict):
        self.client = Spot(key=config.get("API-Key"), secret=config.get("Secret-Key")) # Init client object with configs.
        self.steps_symbols = [
            {"couple": ["DOT", "RUB"], "side": "BUY"},
            {"couple": ["DOT", "USDT"], "side": "SELL"},
            {"couple": ["USDT", "RUB"], "side": "SELL"}
        ] # This is main steps for create orders.
        self.remainder = 50 # Remainder balance. Default is roubles.
        self.percent = 0.1 # Percent value.

    def current_balance(self) -> float:
        """The function takes all value of coins from client balance and return generated balance
        in the dollar value.

        Params
        ------
            Non

        Returns
        -------
            balance : float
                Current balance of client.
        """

        balance: float = 0.0 # Init balance variable with value. Default is 0.0

        for coin in self.client.account().get("balances"):
            asset, free, locked = coin.values() # Init asset and free variables.

            # Check free for quantity.
            if float(free) > 0:
                # Check asset. Must not be in rub or usdt value if it another coins.
                if not asset in ("RUB", "USDT",):
                    try:
                        price: float = float(self.depth(symbol=f"{asset}USDT", limit=1).get("bids")[0][0]) # Get price from api.
                        qty: float = float(free) * price # Generated qty from coins in the dollar value.
                        balance+=qty # Add the quantity to the balance value.
                    except:
                        pass
                elif asset == "USDT":
                    balance+=float(free) # Add the quantity to the balance value. Default is dollar value.
        return balance

    def get_qty_by_symbol(self, symbol: str) -> float:
        """The function takes quantity by symbol from balance and checking for symbol.\n
        If symbol equals asset then return quantity.

        Params
        ------
            symbol : str
                The symbol of coin.

        Returns
        -------
            qty : float
                Current quantity of coin.
        """

        qty: float = float([coin.get("free") for coin in self.client.account().get("balances") if symbol == coin.get("asset")][0])
        return qty

    def create_new_order(self, **kwargs) -> dict:
        """The function create new order.

        Params
        ------
            kwargs : dict
                The kwargs structure consists of symbol, side, type, quantity.
                Default values is None, None, Market, None.

        Returns
        -------
            response : dict
                The main response with all values from api.
        """

        try:
            response = self.client.new_order(**kwargs) # Api response.
            return response
        except Exception as e:
            raise OrderError(e)

    def depth(self, save_to_exel: bool = False, symbol: str = None, limit: int = None) -> dict:
        """The function takes depths by symbol and limit value.

        Params
        ------
            save_to_excel : bool
                If you need to save the depths in an excel file.
            symbol : str
                Default is None. Symbol of coin.
            limit : int
                Default is None. Quantity of limit depths.

        Returns
        -------
            depths : dict
                All the depths.
        """

        if not limit:
            raise DepthError("limit value is empty")
        elif not symbol:
            raise DepthError("symbol value is empty")

        try:
            depths = self.client.depth(symbol=symbol, limit=limit) # Get all depths from API.
            if save_to_exel:
                df = pd.DataFrame(depths)
                df.to_excel("depths.xlsx") # Save depths.
            return depths
        except Exception as e:
            raise DepthError(e)

    def my_trades(self, symbol: str = None) -> list:
        """The function takes all client trades.
        Time format: dt.fromtimestamp(int(str(trade["time"])[:-3])).strftime("%Y-%m-%d %H:%M:%S")

        Params
        ------
            symbol : str
                Default is None. Symbol of coin.

        Returns
        -------
            trades : list
                The all trades by symbol from client.
        """

        try:
            trades = self.client.my_trades(symbol=symbol) # Get all trades from client by symbol.
            return trades
        except Exception as e:
            raise TradesError(e)

    def trade_fee(self, symbol: str = None) -> list:
        """The function takes trade fee by symbol.

        Params
        ------
            symbol : str
                Default is None. Symbol of coin.

        Returns
        -------
            fee : list
                The trade fee. May generated the order percent.
        """

        if not symbol:
            raise TradesError("symbol value is empty")

        fee = self.client.trade_fee(symbol=symbol) # Get tarde fee.
        return fee

    def get_price_by_symbol(self, symbol: str = None, limit: int = 3) -> float:
        """The function get price by symbol.

        Params
        ------
            symbol : str
                Default is None. Symbol of coin.
            limit : int
                Quantity prices from orderbook.

        Returns
        -------
            price : float
                Return arithmetic mean price.
        """

        price: float = 0.0
        bids = self.depth(symbol=symbol, limit=limit).get("bids")
        for n in bids:
            price+=float(n[0]) # Add price of coin. Different value with each position.
        return to_float_format(price/limit)

    def stream(self):
        get_price = self.get_price_by_symbol # (Function object) Gets the price of a symbol.
        get_qty = self.get_qty_by_symbol     # (Function object) Gets the balance value of a symbol.
        to_float = to_float_format           # (Function object) Convert value to float type.
        percent = self.get_percent           # (Function object) Get percent.

        params = {
            "symbol": None,
            "side": None,
            "type": "MARKET",
            "quantity": None
        }

        count_iter: int = 0 # Count iteration steps. Before cycle value eqauls is 0
        before_commission: float = 0.0 # Commission value before cycle. Value equals is 0

        while True:
            cycle_start_time = dt.now() # Start time.
            is_rouble_step = True # Rouble step while iterating. Default: True.
            roubles = get_qty(symbol="RUB") - self.remainder # Roubles balance without remainder.
            logger.info(F"Начальный баланс: {to_float(roubles)}₽") # Show balance value with remainder.

            for step in self.steps_symbols:
                couple: list = step.get("couple") # Get couple from steps value.
                symbol: str = "".join(couple)     # Join couple in the symbol.

                params["symbol"] = symbol         # Set a symbol value in the params.
                params["side"] = step.get("side") # Set a side value in the params.

                if not couple[0] in ("USDT", "RUB",):
                    repeat_price = get_price("DOTUSDT")
                    if is_rouble_step:
                        before_count_exchng = to_float(roubles / get_price(symbol=symbol)) # Generated count exchange.
                        order_commission = to_float(percent((before_count_exchng * self.percent / 100) * repeat_price, is_dollar=True)) # Generated commission per order.
                        before_commission+=order_commission # Add commissiom value per order to the main commission value.
                        params["quantity"] = before_count_exchng # Set quantity in the params.
                        is_rouble_step=False # Set False value for var because next step must be another coin.
                        resp_start_time = dt.now() # Start time.
                        response = self.create_new_order(**params)
                        resp_end_time = (dt.now() - resp_start_time).total_seconds() # End time.
                        logger.info(F"1 ITER Время выполнения (секунды) > {resp_end_time} => {response}")
                    else:
                        params["quantity"] = before_count_exchng # Set quantity in the params.
                        before_count_exchng = to_float(before_count_exchng * repeat_price) # Generated count exchange.
                        order_commission = to_float(percent(before_count_exchng * self.percent / 100, is_dollar=True)) # Generated commission per order.
                        before_commission+=order_commission # Add commissiom value per order to the main commission value.
                        resp_start_time = dt.now() # Start time.
                        response = self.create_new_order(**params)
                        resp_end_time = (dt.now() - resp_start_time).total_seconds() # End time.
                        logger.info(F"2 ITER Время выполнения (секунды) > {resp_end_time} => {response}")
                elif couple[0] == "USDT":
                    # Set quantity in the params and convert to integer format because last order to support integer type.
                    params["quantity"] = to_integer_format(before_count_exchng)
                    before_count_exchng = before_count_exchng * to_float(get_price(symbol=symbol)) # Generated count exchange.
                    order_commission = to_float(percent(before_count_exchng)) # Generated commission per order.
                    before_commission+=order_commission # Add commissiom value per order to the main commission value.
                    resp_start_time = dt.now() # Start time.
                    response = self.create_new_order(**params)
                    resp_end_time = (dt.now() - resp_start_time).total_seconds() # End time.
                    logger.info(F"3 ITER Время выполнения (секунды) > {resp_end_time} => {response}")
                    is_rouble_step = True # Set True value for var because next step must be with roubles.

            before_profit = "{:0.5f}".format(((before_count_exchng - before_commission) * 100 / roubles) - 100)

            logger.info((
                F"Конечный баланс: {before_count_exchng - before_commission}₽; "
                F"Комиссия: {to_float(before_commission)}₽; "
                F"Потенциальный профит: {before_profit}%"
                )
            )

            cycle_end_time = (dt.now() - cycle_start_time).total_seconds() # End time.
            logger.info(F"Operation time (seconds): {cycle_end_time}\n")

            # Reset varibales
            before_commission = 0.0
            cycle_end_time = None

            count_iter+=1
            if count_iter == 5:
                break

    def get_percent(self, qty: str = None, is_dollar: bool = False) -> float:
        """The function generates a percent per order. The percent value is 0.1

        Params
        ------
            qty : str
                The quantity of coins upcoming from the api. Default is None.

            is_dollar : bool
                Checking qty for dollar value. Default is False.

        Returns
        -------
            qty : float
                The quantity of coins upcoming from the api but converted to float type.
        """

        if is_dollar:
            start_time = dt.now() # Start time.
            qty: float = qty * self.get_price_by_symbol(symbol="USDTRUB")
            end_time = (dt.now() - start_time).total_seconds() # End time.
            logger.info(F"Стакан на USDTRUB для расчета комиссии запрошен > Время (секунды): {end_time}")
        else:
            qty: float = qty * self.percent / 100
        return qty