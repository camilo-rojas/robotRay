#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 04 2021
robotRay server v1.0
@author: camilorojas

Golden Strategy

Process for module
1. Evaluate SMA 200 and SMA 50 to find if there are any cross overs
2. In case of a golden cross over inform owner
3. In case or death cross over inform owner

"""
import sys
import os
from tqdm import tqdm
import pandas as pd
import datetime


class rrGoldenStrategy:
    def __init__(self):
        # starting common services
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        # starting logging
        from rrlib.rrLogger import logger
        self.log = logger()
        # starting backend services
        from rrlib.rrDb import rrDbManager
        self.db = rrDbManager()
        # starting ini parameters
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        self.log.logger.debug("  Golden Strategy module starting.  ")

    def evaluateProspects(self):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrDb import IntradayStockData
        from rrlib.rrDb import StockData
        try:
            for stock in IntradayStockData.select():
                # for stock in tqdm(IntradayStockData.select(), desc="Getting SMAs of Stock Data:", unit="Stock", ascii=False, ncols=120, leave=False)
                st = pd.DataFrame(list(StockData.select(StockData.sma50, StockData.sma200, StockData.timestamp).where(
                    StockData.stock == stock.stock).order_by(StockData.id.desc()).dicts()))
                sma50 = st.sma50
                sma200 = st.sma200
                times = st.timestamp
                # get stock data from 2 days earlier to find golden cross or death cross
                try:
                    for i in [i for i, x in enumerate(times) if x < (datetime.datetime.now()-datetime.timedelta(days=2))]:
                        position = i
                        break
                    # find trend
                    sma200now = float(sma200[0].strip("%"))/100
                    sma200old = float(sma200[position].strip("%"))/100
                    sma50now = float(sma50[0].strip("%"))/100
                    sma50old = float(sma50[position].strip("%"))/100

                    if sma200now > sma50now:
                        trend = "downtrend"
                    elif sma200now < sma50now:
                        trend = "uptrend"

                    # look for golden or death and raise communication
                    if sma200now > sma50now and sma200old < sma50old:
                        m200 = ("SMA200 was "+str(sma200old)+", and now is "+str(sma200now))
                        m50 = ("SMA50 was "+str(sma50old)+", and now is "+str(sma50now))
                        self.log.logger.info(
                            "  Golden Strategy found a DEATH CROSS "+trend+" in:"+stock.stock)
                        self.communicateProspects(stock.stock, "Death Cross")
                    elif sma200now < sma50now and sma200old > sma50old:
                        self.log.logger.info(
                            "  Golden Strategy found a GOLDEN CROSS "+trend + " in:"+stock.stock)
                        self.communicateProspects(stock.stock, "Golden Cross "+m200+", "+m50)
                    self.log.logger.debug("Stock:"+stock.stock+", is "+trend+", 50:"+str(sma50[0])+", "+str(sma50[position]) + ", 200:" + str(
                        sma200[0])+", "+str(sma200[position])+"; time:"+str(times[0])+", "+str(times[position]))
                except Exception:
                    self.log.logger.warning("    Golden Strategy for " +
                                            stock.stock+", not enough historic info")

        except Exception as e:
            self.log.logger.error("     Golden Strategy evaluation error:")
            self.log.logger.error(e)

    def communicateProspects(self, stock, gord):
        from rrlib.rrIFTTT import rrIFTTT
        from rrlib.rrTelegram import rrTelegram
        try:
            report = {}
            report["value1"] = "Golden Strategy: Prospect Found: Stock:"+stock
            report["value2"] = "Found a: "+gord
            report["value3"] = "Good luck! "
            self.log.logger.debug(
                "    Communicator , invoking with these parameters "+str(report))
            self.db.updateServerRun(prospectsFound="Yes")
            try:
                rrIFTTT().send(report)
                rrTelegram().sendMessage(
                    str(report["value1"])+" | "+str(report["value2"])+" | "+str(report["value3"]))

            except Exception as e:
                self.log.logger.error(
                    "     Golden Strategy communicating error")
                self.log.logger.error(e)
        except Exception as e:
            self.log.logger.error(
                "     Golden Strategy prospect communicator error")
            self.log.logger.error(e)
