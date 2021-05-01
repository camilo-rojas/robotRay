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
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        # db filename to confirm it exists
        self.funds = config.get('portfolio', 'funds')
        self.R = config.get('portfolio', 'R')
        self.monthlyPremium = config.get('portfolio', 'monthlyPremium')
        self.BP = config.get('portfolio', 'BP')
        # Get datsource from pubic or ib
        self.source = config.get('datasource', 'source')

    def switchSource(self, source):
        if source == "ib":
            self.source = "ib"
            self.log.logger.info(
                "  Portfolio switching from Public to Interactive Brokers")
        elif source == "public":
            self.source = "public"
            self.log.logger.info(
                "  Portfolio switching from Interactive Brokers to Public")
        else:
            self.source = "public"
            self.log.warning(
                "  Portfolio switching allows ib for Interactive Brokers or Public for finviz / yahoo, public by default")

    def getPositions(self):
        df = pd.DataFrame()
        if self.source == "ib":
            from rrlib.rrDFIB import IBConnection
            self.ib = IBConnection()
            self.log.logger.info("    About to retreive Portfolio")
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
            from pprint import pprint
            self.ib = IBConnection()
            self.log.logger.info("    About to retreive Portfolio")
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
            return df
