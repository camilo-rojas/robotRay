#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 04 2021
robotRay server v1.0
@author: camilorojas

Backtrader for Golden cross and Death cross Strategy


"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader as bt
import datetime
import math


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
        self.commission = float(config.get('backtrader', 'commission'))
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
        # set commision statement
        self.cerebro.broker.setcommission(self.commission)
        # Add a FixedSize sizer according to the stake
        self.cerebro.addsizer(bt.sizers.FixedSize, stake=10)
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
    params = (
        ('exitbars', 5),
        ('smashort', 50),
        ('smalong', 200),
        ('maxinv', 3)
    )

    def __init__(self):
        # start logger service
        from rrlib.rrLogger import logger
        self.log = logger()
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        # To keep track of pending orders
        self.order = None
        self.buyprice = None
        self.buycomm = None
        # Add a MovingAverageSimple indicator
        self.sma1 = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.smashort)
        self.sma2 = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.smalong)
        bt.indicators.MACDHisto(self.datas[0])
        rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.SmoothedMovingAverage(rsi, period=10)
        bt.indicators.ATR(self.datas[0], plot=False)
        self.crossover = bt.indicators.CrossOver(self.sma1, self.sma2)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log.logger.debug('BUY EXECUTED, %.2f' % order.executed.price)
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log.logger.debug('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log.logger.debug('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log.logger.debug('OPERATION PROFIT, GROSS '+str(trade.pnl) +
                              ', NET ' + str(trade.pnlcomm))

    def next(self):
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return
        # Check if we are in the market
        if not self.position:
            if self.crossover > 0:
                self.size = math.floor((float(self.params.maxinv)*float(self.broker.cash)) /
                                       (self.data.close*100))
                self.log.logger.debug('BUY CREATE, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(size=self.size)
        else:
            # Already in the market ... we might sell
            if self.crossover < 0:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log.logger.debug('SELL CREATE, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.close()
