steps = [
    {"couple": ["DOT", "RUB"], "side": "BUY"},
    {"couple": ["DOT", "USDT"], "side": "SELL"},
    {"couple": ["USDT", "RUB"], "side": "SELL"}
] # This is main steps for create orders.

order_params = {
    "symbol": None,
    "side": None,
    "type": "MARKET",
    "quantity": None
}

BLOCKED_COUPLE_PART = ("USDT", "RUB",)