#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 04 2021
robotRay server v1.0
@author: camilorojas

Backtrader strategy classes

Process for module
1. Gather data from yfinance the data for the stocks
3. Call the strategy backtrader

Pending
2. Gather data from options (?)

"""

import yfinance as yf
import pandas as pd
import peewee as pw
import datetime
import sys
import os
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
        from rrlib.rrGoldenBt import rrGoldenBt
        rrGoldenBt().run()

    def getHistoricData(self, stock):
        df = pd.DataFrame(historicData.select().where(historicData.stock == stock).dicts())
        df.drop('timestamp', inplace=True, axis=1)
        df.drop('id', inplace=True, axis=1)
        df.drop('stock', inplace=True, axis=1)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', drop=True, inplace=True)
        return df

    def downloadStockData(self):
        stocks = self.db.getStocks()
        historicData.drop_table(True)
        historicData.create_table()
        SQLITE_MAX_VARIABLE_NUMBER = self.max_sql_variables()
        for index, stock in tqdm(stocks.iterrows(), desc="  Getting Historic Data", unit="Stock", ascii=False, ncols=120, leave=False):
            try:
                yfstock = yf.Ticker(stock['ticker'])
                df = yfstock.history(period=self.timeframe)
                df['stock'] = stock['ticker']
                df['date'] = df.index
                df.rename(columns={'stock': 'stock', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close',
                                   'Volume': 'volume', 'Dividends': 'dividends', 'Stock Splits': 'stocksplits', 'Date': 'date'}, inplace=True)
                page = int((len(df)*len(df.columns)*1.5))
                size = int(page // SQLITE_MAX_VARIABLE_NUMBER)
                if size > 0:
                    increment = int(len(df)//size)
                else:
                    increment = -1
                if size > 0:
                    for i in range(0, len(df), increment):
                        # print("i:"+str(i)+", i+increment"+str(i+increment))
                        historicData.insert_many(df.to_dict(orient='records')[
                            i:i+increment]).execute()
                else:
                    historicData.insert_many(df.to_dict(orient='records')).execute()

            except Exception as e:
                self.log.logger.warning("Problem downloading data")
                self.log.logger.warning(e)

    def max_sql_variables(self):
        import sqlite3
        db = sqlite3.connect(':memory:')
        cur = db.cursor()
        cur.execute('CREATE TABLE t (test)')
        low, high = 0, 100000
        while (high - 1) > low:
            guess = (high + low) // 2
            query = 'INSERT INTO t VALUES ' + ','.join(['(?)' for _ in
                                                        range(guess)])
            args = [str(i) for i in range(guess)]
            try:
                cur.execute(query, args)
            except sqlite3.OperationalError as e:
                if "too many SQL variables" in str(e):
                    high = guess
                else:
                    raise
            else:
                low = guess
        cur.close()
        db.close()
        return low


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
