#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 04 2021
robotRay server v1.0
@author: camilorojas

Portfolio classes

Process for module
1. if source is ib then get portfolio total from ib
2. if source is public then get portfolio total from .ini file
3. class lifecycle methods

"""
import pandas as pd


class rrPortfolio:
    def __init__(self):
        # Starting common services
        from rrlib.rrLogger import logger, TqdmToLogger
        # Get logging service
        self.log = logger()
        self.tqdm_out = TqdmToLogger(self.log.logger)
        self.log.logger.debug("  Backtrader starting.  ")
        # starting ini parameters
        import configparser
        import math
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        # db filename to confirm it exists
        self.source = config.get('datasource', 'source')
        if self.source == "ib":
            self.funds = str(self.getAvailableFunds())
        else:
            self.funds = config.get('portfolio', 'funds')
        if self.source == "ib":
            self.R = str(int(math.ceil(self.getAvailableFunds()*0.005 / 100.0)) * 100)
        else:
            self.R = config.get('portfolio', 'R')
        self.monthlyPremium = config.get('portfolio', 'monthlyPremium')
        if self.source == "ib":
            self.BP = float(self.getBuyingPower())
        else:
            self.BP = config.get('portfolio', 'BP')
        # Get datsource from pubic or ib

    def switchSource(self, source):
        import configparser
        import math
        config = configparser.ConfigParser()
        if source == "ib":
            self.source = "ib"
            self.funds = str(self.getAvailableFunds())
            self.BP = float(self.getBuyingPower())
            self.R = str(int(math.ceil(self.getAvailableFunds()*0.005 / 100.0)) * 100)
            self.log.logger.info(
                "  Portfolio switching from Public to Interactive Brokers")
        elif source == "public":
            self.source = "public"
            self.funds = config.get('portfolio', 'funds')
            self.R = config.get('portfolio', 'R')
            self.BP = config.get('portfolio', 'BP')
            self.log.logger.info(
                "  Portfolio switching from Interactive Brokers to Public")
        else:
            self.source = "public"
            self.funds = config.get('portfolio', 'funds')
            self.R = config.get('portfolio', 'R')
            self.BP = config.get('portfolio', 'BP')
            self.log.warning(
                "  Portfolio switching allows ib for Interactive Brokers or Public for finviz / yahoo, public by default")

    def getPositions(self):
        df = pd.DataFrame()
        if self.source == "ib":
            from rrlib.rrDFIB import IBConnection
            self.ib = IBConnection()
            self.log.logger.debug("    About to retreive Portfolio")
            if not self.ib.isConnected():
                self.ib.connect()
            pos = self.ib.getPositions()
            df = pd.DataFrame(pos)
            df['symbol'] = ""
            pd.options.mode.chained_assignment = None  # default='warn'
            for i in range(len(df)):
                df['symbol'][i] = pos[i][1].symbol
            df.drop('contract', inplace=True, axis=1)
        else:
            # get Db positions
            pass
        return df

    def getAccount(self):
        if self.source == "ib":
            from rrlib.rrDFIB import IBConnection
            self.ib = IBConnection()
            self.log.logger.debug("    About to retreive Portfolio")
            if not self.ib.isConnected():
                self.ib.connect()
            # AvailableFunds, BuyingPower, TotalCashValue, NetLiquidation, ExcessLiquidity,
            # FullInitMarginReq
            # StockMarketValue, OptionMarketValue, UnrealizedPnL, RealizedPnL
            acct = pd.DataFrame(self.ib.ib.accountSummary())
            df = pd.DataFrame({"key": ["AvailableFunds", "BuyingPower", "TotalCashValue", "NetLiquidation",   "ExcessLiquidity", "FullInitMarginReq", "StockMarketValue", "OptionMarketValue", "UnrealizedPnL", "RealizedPnL"],
                               "value": [acct[acct.tag == "AvailableFunds"].value.item(), acct[acct.tag == "BuyingPower"].value.item(), acct[acct.tag == "TotalCashValue"].value.item(), acct[acct.tag == "NetLiquidation"].value.item(), acct[acct.tag == "ExcessLiquidity"].value.item(), acct[acct.tag == "FullInitMarginReq"].value.item(), acct.loc[(acct['account'] == 'All') & (
                                   acct["tag"] == "StockMarketValue"), 'value'].values[0], acct.loc[(acct['account'] == 'All') & (
                                       acct["tag"] == "OptionMarketValue"), 'value'].values[0], acct.loc[(acct['account'] == 'All') & (
                                           acct["tag"] == "UnrealizedPnL"), 'value'].values[0], acct.loc[(acct['account'] == 'All') & (
                                               acct["tag"] == "RealizedPnL"), 'value'].values[0]]})
        else:
            # get account info public
            pass
        return df

    def getBuyingPower(self):
        if self.source == "ib":
            # get
            df = self.getAccount()
            buyingPower = float(df[df['key'] == 'BuyingPower'].value)
        else:
            # get trades info public
            pass
        return buyingPower

    def getAvailableFunds(self):
        if self.source == "ib":
            df = self.getAccount()
            availableFunds = float(df[df['key'] == 'AvailableFunds'].value)
        else:
            # get trades info public
            pass
        return availableFunds

    def getCash(self):
        if self.source == "ib":
            df = self.getAccount()
            cash = float(df[df['key'] == 'TotalCashValue'].value)
        else:
            # get trades info public
            pass
        return cash

    def getUnrealizedPNL(self):
        if self.source == "ib":
            df = self.getAccount()
            unrpnl = float(df[df['key'] == 'UnrealizedPnL'].value)
        else:
            # get trades info public
            pass
        return unrpnl

    def getRealizedPNL(self):
        if self.source == "ib":
            df = self.getAccount()
            rpnl = float(df[df['key'] == 'RealizedPnL'].value)
        else:
            # get trades info public
            pass
        return rpnl

    def getTrades(self):
        if self.source == "ib":
            from rrlib.rrDFIB import IBConnection
            self.ib = IBConnection()
            self.log.logger.debug("    About to retreive trades")
            if not self.ib.isConnected():
                self.ib.connect()
            trades = pd.DataFrame(self.ib.ib.trades())
            df = trades
        else:
            # get trades info public
            pass
        return df

    def getOpenTrades(self):
        if self.source == "ib":
            from rrlib.rrDFIB import IBConnection
            self.ib = IBConnection()
            self.log.logger.debug("    About to retreive open trades")
            if not self.ib.isConnected():
                self.ib.connect()
            trades = pd.DataFrame(self.ib.ib.openTrades())
            df = trades
        else:
            # get trades info public
            pass
        return df

    def getOpenOrders(self):
        if self.source == "ib":
            from rrlib.rrDFIB import IBConnection
            self.ib = IBConnection()
            self.log.logger.debug("    About to retreive open orders")
            if not self.ib.isConnected():
                self.ib.connect()
            trades = pd.DataFrame(self.ib.ib.openOrders())
            df = trades
        else:
            # get trades info public
            pass
        return df

    def getOrders(self):
        if self.source == "ib":
            from rrlib.rrDFIB import IBConnection
            self.ib = IBConnection()
            self.log.logger.debug("    About to retreive open orders")
            if not self.ib.isConnected():
                self.ib.connect()
            trades = pd.DataFrame(self.ib.ib.orders())
            df = trades
        else:
            # get trades info public
            pass
        return df
