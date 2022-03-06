from json import loads
from datetime import datetime as dt

import pandas as pd

with open(r"orders_100.txt", "r") as f:
    orders = f.readlines()

orders_dct: dict = {}
for order in orders:
    try:
        order_row: dict = loads(order.strip().replace("'", "\""))
        symbol: str = order_row.get("symbol")
        orderId: int = order_row.get("orderId")
        transactTime: str = dt.fromtimestamp(int(str(order_row.get("transactTime"))[:-3])).strftime("%Y-%m-%d %H:%M:%S")
        side: str = order_row.get("side")
        fills: str = order_row.get("fills")[0] # Is not use in dict.
        price: str = fills.get("price")
        count: str = fills.get("qty")
        commission: str = fills.get("commission")
        commissionAsset: str = fills.get("commissionAsset")
        orders_dct[orderId] = dict(symbol=symbol, transactTime=transactTime, side=side, price=price, count=count, commission=commission, commissionAsset=commissionAsset)
    except Exception as e:
        print(e)
df = pd.DataFrame(orders_dct)
df.to_excel("_orders.xlsx")