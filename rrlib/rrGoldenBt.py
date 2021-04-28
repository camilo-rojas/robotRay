#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 04 2021
robotRay server v1.0
@author: camilorojas

Backtrader for Golden cross and Death cross Strategy


"""

import backtrader as bt
import matplotlib
import datetime
import threading


class rrGoldenBt:
    def __init__(self, symbol):
        # Starting common services
        from rrlib.rrLogger import logger, TqdmToLogger
        from rrlib.rrDb import rrDbManager
        from rrlib.rrBacktrader import rrBacktrader
        from rrlib.rrPortfolio import rrPortfolio
        # Get logging service
        self.log = logger()
        self.tqdm_out = TqdmToLogger(self.log.logger)
        self.log.logger.debug("  Backtrader starting.  ")
        # startup parameter
        self.symbol = symbol
        # startup backtrading db
        self.btdb = rrBacktrader()
        self.portfolio = rrPortfolio()
        # starting ini parameters
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        # max investment in % terms of porfolio
        self.maxinv = config.get('backtrader', 'maxinv')
        self.timeframe = config.get('backtrader', 'timeframe')
        # Generate Cerebro
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(float(self.portfolio.funds))
        # Get portfoilo total

    def run(self):
        # add data feed stored in database
        historicdata = self.btdb.getHistoricData(self.symbol)
        feed = bt.feeds.PandasData(dataname=historicdata)
        self.cerebro.adddata(feed)
        # load strategy for backtesting
        self.cerebro.addstrategy(GoldenStrategy)
        # start balance for performance testing
        initialbalance = self.cerebro.broker.getvalue()
        # try to run the cerebro strategies
        try:
            self.cerebro.run()
        except Exception as e:
            self.log.logger.warning("  Cerebro Run exception")
            self.log.logger.warning(e)
        # get final balance for cerebro strategy
        finalbalance = self.cerebro.broker.getvalue()
        self.log.logger.info(
            f'   Golden Strategy BT for {self.symbol} generated a {round((finalbalance-initialbalance)/initialbalance*100,2)}%')
        # plot the strategy if generates outstanding value
        if self.symbol == "CRM":
            # remove ./venv/lib/python3.9/site-packages/backtrader/plot/locator.py warning import
            self.cerebro.plot()


class GoldenStrategy(bt.Strategy):

    def __init__(self):
        # start logger service
        from rrlib.rrLogger import logger
        self.log = logger()
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        # To keep track of pending orders
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log.logger.debug('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log.logger.debug('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log.logger.debug('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def next(self):
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return
        # Check if we are in the market
        if not self.position:
            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.dataclose[-1]:
                # current close less than previous close
                if self.dataclose[-1] < self.dataclose[-2]:
                    # previous close less than the previous close
                    # BUY, BUY, BUY!!! (with default parameters)
                    self.log.logger.debug('BUY CREATE, %.2f' % self.dataclose[0])
                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()
        else:
            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + 5):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log.logger.debug('SELL CREATE, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
