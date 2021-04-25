#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 04 2021
robotRay server v1.0
@author: camilorojas

Backtrader strategy classes

Process for module
1. Gather data from yfinance the data for the stocks

"""

import yfinance as yf
import pandas as pd
import peewee as pw
import datetime
import sys
import os
import time
from tqdm import tqdm

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
db = pw.SqliteDatabase('rrBt.db')


class rrBacktrader:
    def __init__(self):
        # Starting common services
        from rrlib.rrLogger import logger, TqdmToLogger
        from rrlib.rrDb import rrDbManager
        # Get logging service
        self.db = rrDbManager()
        self.log = logger()
        self.tqdm_out = TqdmToLogger(self.log.logger)
        self.log.logger.debug("  Backtrader starting.  ")
        # starting ini parameters
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        # db filename to confirm it exists
        self.dbFilename = config.get('backtrader', 'filename')
        self.timeframe = config.get('backtrader', 'timeframe')
        self.initializeDb()
        # Get datsource from pubic or ib
        self.source = config.get('datasource', 'source')
        # Get verbose option boolean
        self.verbose = config.get('datasource', 'verbose')

    def initializeDb(self):
        historicData.create_table()

    def btSellPuts(self):
        pass

    def btGolden(self):
        pass

    def downloadStockData(self):
        stocks = self.db.getStocks()
        for index, stock in tqdm(stocks.iterrows(), desc="  Getting Historic Data", unit="Stock", ascii=False, ncols=120, leave=False):
            try:
                historicData.drop_table(True)
                historicData.create_table()
                yfstock = yf.Ticker(stock['ticker'])
                df = yfstock.history(period=self.timeframe)
                df['stock'] = stock['ticker']
                df['date'] = df.index
                df.rename(columns={'stock': 'stock', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close',
                                   'Volume': 'volume', 'Dividends': 'dividends', 'Stock Splits': 'stocksplits', 'Date': 'date'}, inplace=True)
                historicData.insert_many(df.to_dict(orient='records')).execute()

            except Exception as e:
                self.log.logger.warning("Problem downloading data")
                self.log.logger.warning(e)


class historicData(pw.Model):
    stock = pw.CharField(null=True)
    timestamp = pw.DateTimeField(null=True, default=datetime.datetime.now())
    date = pw.DateField(null=True)
    open = pw.FloatField(null=True)
    high = pw.FloatField(null=True)
    low = pw.FloatField(null=True)
    close = pw.FloatField(null=True)
    volume = pw.FloatField(null=True)
    dividends = pw.FloatField(null=True)
    stocksplits = pw.FloatField(null=True)

    class Meta:
        database = db
        db_table = "historicData"
