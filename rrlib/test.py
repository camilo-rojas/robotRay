

import sys
import os
import pandas as pd

if True:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from rrlib.rrPortfolio import rrPortfolio
    from rrlib.rrDFIB import StockDFIB
    from rrlib.rrDFIB import OptionDFIB
    from rrlib.rrDFPublic import StockDFPublic
    from rrlib.rrDFPublic import OptionDFPublic
    from rrlib.rrDataFetcher import OptionDataFetcher as optFetcher
    from rrlib.rrDailyScan import rrDailyScan as ds
    from rrlib.rrBacktrader import rrBacktrader as bt

pd.set_option('display.max_columns', None)
ds().dailyScan()

"""
stockIB = StockDFIB("AAPL")
print(stockIB.getIntradayData())
print(stockIB.getData())
stockP = StockDFPublic("AAPL")
print(stockP.getIntradayData())
print(stockP.getData())

option = OptionDFIB("CRM")
print(option.getData(3, 160))

op = OptionDFPublic("CRM")
print(op.getData(3, 160))
p = rrPortfolio()
p.switchSource("ib")
option = OptionDFIB("CRM")
print(option.getData(3, 160))
print(stock.getIntradayData())
pd.set_option('display.max_columns', None)
print(p.R)
print(p.BP)
print(p.funds)
print(p.getAccount())
print(p.getBuyingPower())
print(p.getRealizedPNL())
print(p.getUnrealizedPNL())
print(p.getCash())
print(p.getAvailableFunds())
strikes = optFetcher("SHOP").getStrikes()
print(strikes)
"""
