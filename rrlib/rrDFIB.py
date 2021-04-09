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
"""

import sys
import os
import pandas as pd


class StockDFIB():

    def __init__(self, symbol):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrLogger import logger
        self.symbol = symbol
        self.log = logger()
        self.log.logger.debug("    Init Stock IB Data Fetcher "+str(symbol))
        # timeout import
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        self.timeout = int(config['urlfetcher']['Timeout'])

    def getData(self):
        self.log.logger.debug("    About to retreive "+self.symbol)
        stock = pd.DataFrame()
        self.log.logger.debug("      For: "+self.symbol+" data:"+str(stock))
        df = pd.DataFrame(stock, columns=['key', 'value'])
        pd.set_option("display.max_rows", None, "display.max_columns", None)
        self.log.logger.debug("   Values loaded: \n"+str(df))
        self.log.logger.debug(
            "    DONE - Stock Public Data Fetcher "+str(self.symbol))
        return df

    def getIntradayData(self):
        self.log.logger.debug("    About to retreive "+self.symbol)
        stock = pd.DataFrame()
        self.log.logger.debug("      For: "+self.symbol+" data:"+str(stock))
        df = pd.DataFrame()
        # df = pd.DataFrame(columns=['stock', 'price', '%Change', '%Volume'])
        df = df.append({'stock': self.symbol, 'price': stock.get('Price'),
                        '%Change': float(stock.get('Change').strip('%'))/100,
                        '%Volume':
                        float(stock.get('Rel Volume'))}, ignore_index=True)
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
        self.timeout = int(config['urlfetcher']['Timeout'])

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
