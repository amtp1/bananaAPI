import sys
import inspect
from binance.error import ClientError
from numpy import isin

class NoTraceBackWithLineNumber(Exception):
    def __init__(self, msg):
        try:
            ln = sys.exc_info()[-1].tb_lineno
            if isinstance(msg, ClientError):
                self.args = "{0.__name__} (line {1}): {2}".format(type(self), ln, msg.args[2]),
        except AttributeError:
            ln = inspect.currentframe().f_back.f_lineno
            self.args = "{0.__name__} (line {1}): {2}".format(type(self), ln, msg),
        sys.exit(self)

class FileError(NoTraceBackWithLineNumber):
    pass

class DepthError(NoTraceBackWithLineNumber):
    pass

class OrderError(NoTraceBackWithLineNumber):
    pass

class TradesError(NoTraceBackWithLineNumber):
    pass

class ExchangeError(NoTraceBackWithLineNumber):
    pass