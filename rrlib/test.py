

import sys
import os
import pandas as pd

if True:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from rrlib.rrPortfolio import rrPortfolio
    print("Start")
    from rrlib.rrDFIB import StockDFIB
    print("Start")

stock = StockDFIB("AAPL")
p = rrPortfolio()
p.switchSource("ib")
stock1 = StockDFIB("CRM")
stock.getIntradayData()
pd.set_option('display.max_columns', None)
print(p.getAccount())
stock1.getIntradayData()
