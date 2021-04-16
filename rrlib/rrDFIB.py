#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 05 04 2021
robotRay server v1.0
@author: camilorojas

Data Fetcher Interactive Brokers will request the information from the following datasources
Stock Data - IB library
Intraday Stock Data - IB library
Option Data - IB library

Pending implementation

getdata return pd[
9 - performance week text with % at the end
15 - perfromance month text with % at the end
20 - shortFloat text % final
21 - performance quarter text with % at the end
26 - short ratio text
27 - performance half year text % final
31 - target price
32 - performance year text % final - TTM_over_TTM
36 - roe text
38 - perf ytd text % final
42 - roi text - TTMROIPCT
43 - w52 high % final text - NHIG precio mayor
44 - beta text
47 - sales 5 year growth text with % at the end - REVTRENDGR 5 años
49 - w52 low % final text - NLOW precio menor
53 - sales quarter after quarter text with % at the end - REVCHNGYR 1 año
61 - relative volume text
62 - previous close text
65 - earnings date text Apr 28 AMC
68 - price text - NPRICE
69 - recomendation analyst(1 sell 5 buy)
70 - sma 20 text % final
71 - sma 50 text % final
72 - sma 200 text % final
74 - performance day text % final
]

getoptiondata return pd [
1 - open price
2 - bid
3 - ask
5 - expiration date
6 - day range
8 - volume
9 - open interest
10 - price
]

"""

import sys
import os
import pandas as pd
from ib_insync import *


class StockDFIB():

    def __init__(self, symbol):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrLogger import logger
        self.symbol = symbol
        self.log = logger()
        self.log.logger.debug("    Init Stock IB Data Fetcher "+str(symbol))
        # ib parameter import
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        self.ib_ip = int(config['ib']['ip'])
        self.ib_port = int(config['ib']['port'])

    def getData(self):
        self.log.logger.info("    About to connect to IB for "+self.symbol)
        ib = IB()
        ib.connect(self.ib_ip, float(self.ib_port), clientId=1)
        self.log.logger.info("    Connected to IB for "+self.symbol)
        stock = Stock(self.symbol, "SMART", "USD")

        self.log.logger.info("    Fetched data from IB for "+self.symbol)

        self.log.logger.debug("      For: "+self.symbol+" data:"+str(stock))
        df = pd.DataFrame(columns=['key', 'value'])
        pd.set_option("display.max_rows", None, "display.max_columns", None)
        self.log.logger.debug("   Values loaded: \n"+str(df))
        self.log.logger.debug(
            "    DONE - Stock Public Data Fetcher "+str(self.symbol))
        return df

    def getIntradayData(self):
        self.log.logger.debug("    About to retreive "+self.symbol)
        df = pd.DataFrame()
        # df = pd.DataFrame(columns=['stock', 'price', '%Change', '%Volume'])
        df = df.append({'stock': 'symbol', 'price': 'Price',
                        '%Change': 'Change price',
                        '%Volume': 'rel volume'
                        }, ignore_index=True)
        self.log.logger.debug("   Values loaded: \n"+str(df))
        self.log.logger.debug(
            "    DONE - Stock Intraday Public Data Fetcher "+str(self.symbol))
        return df


class OptionDFIB():

    def __init__(self, symbol):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrLogger import logger
        self.symbol = symbol
        self.log = logger()
        self.log.logger.debug("    Init Option IB Data Fetcher for "+symbol)
        # timeout import
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        self.ib_ip = int(config['ib']['ip'])
        self.ib_port = int(config['ib']['port'])

    # Strike int, month is int and the number of months after today
    def getData(self, month, strike):
        # https://finance.yahoo.com/quote/WDAY200117P00160000
        # Get the put value for specified month 3-8
        month = int(month)
        df = pd.DataFrame(columns=['key', 'value'])
        if (3 <= month <= 8):
            # get option data
            self.log.logger.debug("    Done Option loaded: \n"+str(df))
            self.log.logger.debug(
                "    Getting Public Option loaded: "+self.symbol+" for month "+str(month))
            return df
        else:
            self.log.logger.error(
                "    Month outside or range, allowed 3-8 months")
            return df
