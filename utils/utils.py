from datetime import datetime as dt

from binance.spot import Spot
import pandas as pd
from logger.logger import logger

from config.config import Config
from .formatting import *
from exceptions.exceptions import *
from .context import *

config = Config()


class Core:
    def __init__(self):
        """Initialize"""

        self.client = Spot(key=config.config.get("API_KEY"), secret=config.config.get("SECRET_KEY")) # Init client object with configs.
        self.remainder = 50 # Remainder balance. Default is roubles.
        self.percent = 0.1 # Percent value.
        self.is_rouble_step = True # Rouble step while iterating. Default: True.

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
                        symbol: str = valid_symbol(asset) # Get valid symbol
                        
                        if symbol:
                            price: float = float(self.depth(symbol=symbol, limit=1).get("bids")[0][0]) # Get price from api.
                            qty: float = float(free) * price # Generated qty from coins in the dollar value.
                            balance+=qty # Add the quantity to the balance value.
                    except Exception as e:
                        logger.error(e)
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

    def trades(self, symbol: str = None, to_excel: bool = False) -> list:
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
            if to_excel:
                self.to_excel(trades)
            return trades # Return account trades
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

    def stream(self, count_iter: int):
        get_price = self.get_price_by_symbol # (Function object) Gets the price of a symbol.
        get_qty = self.get_qty_by_symbol     # (Function object) Gets the balance value of a symbol.
        to_float = to_float_format           # (Function object) Convert value to float type.
        percent = self.get_percent           # (Function object) Get percent.

        before_commission: float = 0.0 # Commission value before cycle. Value equals is 0
        true_potential_profit_values = []
        time_true_potential_profit_values = []
        false_potential_profit_values = []
        counter = 0
        while True:
            cycle_start_time = dt.now() # Start time.
            roubles = self.get_qty_by_symbol(symbol="RUB") - self.remainder # Roubles balance without remainder.
            logger.info(F"Начальный баланс: {to_float_format(roubles)}₽") # Show balance value with remainder.

            if roubles < 0:
                return logger.error("Операция не может быть выполнена при отрицательном балансе!")
            else:
                template_steps = []
                for i, step in enumerate(steps):
                    couple: list = step.get("couple") # Get couple from steps value.
                    symbol: str = "".join(couple)     # Join couple in the symbol.

                    order_params["symbol"] = symbol         # Set a symbol value in the params.
                    order_params["side"] = step.get("side") # Set a side value in the params.

                    if not couple[0] in ("USDT", "RUB",):
                        repeat_price = self.get_price_by_symbol("DOTUSDT")
                        if self.is_rouble_step:
                            before_count_exchng = to_float(roubles / get_price(symbol=symbol)) # Generated count exchange.
                            order_commission = to_float(percent((before_count_exchng * self.percent / 100) * repeat_price, is_dollar=True)) # Generated commission per order.
                            before_commission+=order_commission # Add commissiom value per order to the main commission value.
                            order_params["quantity"] = before_count_exchng # Set quantity in the params.
                            self.is_rouble_step=False # Set False value for var because next step must be another coin.
                            self.temp_steps(**order_params)
                        else:
                            order_params["quantity"] = before_count_exchng # Set quantity in the params.
                            before_count_exchng = to_float(before_count_exchng * repeat_price) # Generated count exchange.
                            order_commission = to_float(percent(before_count_exchng * self.percent / 100, is_dollar=True)) # Generated commission per order.
                            before_commission+=order_commission # Add commissiom value per order to the main commission value.
                            self.temp_steps(**order_params)
                    elif couple[0] == "USDT":
                        # Set quantity in the params and convert to integer format because last order to support integer type.
                        order_params["quantity"] = to_integer_format(before_count_exchng)
                        before_count_exchng = before_count_exchng * to_float(get_price(symbol=symbol)) # Generated count exchange.
                        order_commission = to_float(percent(before_count_exchng)) # Generated commission per order.
                        before_commission+=order_commission # Add commissiom value per order to the main commission value.
                        self.is_rouble_step = True # Set True value for var because next step must be with roubles.
                        template_steps = self.temp_steps(**order_params)

                potential_profit = ((before_count_exchng - before_commission) * 100 / roubles) - 100
                potential_profit_fmt = "{:0.5f}".format(potential_profit)

                if potential_profit > 0:
                    true_potential_profit_values.append(potential_profit)
                    logger.info((
                        F"Конечный баланс: {before_count_exchng - before_commission}₽; "
                        F"Комиссия: {to_float(before_commission)}₽; "
                        F"Потенциальный профит: {potential_profit_fmt}%"
                    )
                    )
                    self.make_template_steps(template_steps)
                else:
                    false_potential_profit_values.append(potential_profit)
                    logger.info(F"Операция не была проведена, так как потенциальный профит отрицательный ({potential_profit_fmt})")

                # Reset varibales
                before_commission = 0.0
                cycle_end_time = None

                cycle_end_time = (dt.now() - cycle_start_time).total_seconds() # End time.
                logger.info("Operation time (seconds): {:.1f} seconds.\n".format(cycle_end_time))

                counter+=1
                if counter == count_iter:
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
            qty: float = qty * self.get_price_by_symbol(symbol="USDTRUB") # Generated quantity after get symbol price.
            end_time = (dt.now() - start_time).total_seconds() # End time.
            logger.info(F"Стакан на USDTRUB для расчета комиссии запрошен > Время (секунды): {end_time}")
        else:
            qty: float = qty * self.percent / 100
        return qty

    def to_excel(self, trades: list):
        """The function writes orders to an excel file

        Params
        ------
            trades : list
                All trades from account

        Returns
        -------
            logger message
        """

        basename = "trades"
        suffix = dt.now().strftime("%y%m%d_%H%M%S")
        filename = "_".join([basename, suffix]) # e.g. 'mylogfile_120508_171442'
        
        df = pd.DataFrame(trades) # Convert data to the DataFrame.
        df.to_excel(F"bdata/{filename}.xlsx", index=False) # Save data in the new file.

        return logger.info(F"File {filename}.xlsx saved in bdata. Path: bdata/{filename}.xlsx")

    def get_response(self, i, **order_params: dict):
        """The function creates a new order and receives an answer and writes in the log file.

        Params
        ------
            **order_params : dict
                Converted data to create an order.

        Returns
        -------
            logger message
        """

        resp_start_time = dt.now() # Start time.
        response = self.create_new_order(**order_params) # Make new request.
        resp_end_time = (dt.now() - resp_start_time).total_seconds() # End time.
        return logger.info(F"{i+1} ITER Время выполнения (секунды) > {resp_end_time} => {response}")

    def make_template_steps(self, template_steps: list):
        """The function is triggered when the potential profit is positive.\n
        The function saves all values to execute an order when the potential profit is positive

        Params
        ------
            template_steps : list
                All template steps.
        """

        # Go through all the steps and execute the query.
        for i, t_step in enumerate(template_steps):
            self.get_response(i, **t_step)

    def temp_steps(self, _o_p = [], **o_p):
        """The function adds all steps to perform them at a positive potential profit.

        Params
        ------
            _o_p : list
                Default empty list. Each step is added to the list during iteration.

            **o_p : dict
                Order params.

        Returns
        -------
            _o_p : list
                List with order params.
        """

        _o_p.append(o_p) # Append order params in the list.
        return _o_p