#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 04 2021
robotRay server v1.0
@author: camilorojas

Daily Scan classes

Process for module
Daily download of the data sources, analyze with technical analysis all
signals that are present in the last 5 days and prepare a report to inform the user

"""

import pandas as pd
import numpy as np
import os
import sys
import talib
from rrlib.rrBacktrader import historicData, rrBacktrader


class rrDailyScan:
    def __init__(self):
        # Starting common services
        from rrlib.rrLogger import logger, TqdmToLogger
        from rrlib.rrDb import rrDbManager
        # Get logging service
        self.db = rrDbManager()
        self.log = logger()
        self.tqdm_out = TqdmToLogger(self.log.logger)
        self.log.logger.debug("  Daily scanner starting.  ")
        # starting ini parameters
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        # set patterns for daily detection
        self.patterns = pd.DataFrame(np.array([
            # ['CDL2CROWS', 'Two Crows', 'Low reversal w conf', '5.7 % ', '35.2 %'],
            ['CDL3BLACKCROWS', '* Three Black Crows *', 'High R2BE', '-0.144', '0.286'],
            ['CDL3INSIDE', 'Three Inside Up/Down', 'Medium Reversal', '0.062', '0.354'],
            ['CDL3LINESTRIKE', '* Three Line Strike *', 'High R2BU', '0.108', '0.369'],
            # ['CDL3OUTSIDE', 'Three Outside Up/Down', 'Medium Reversal', '0.051', '0.35'],
            ['CDL3STARSINSOUTH', 'Three Stars In The South', 'Rare Medium R2BU w conf', '0.20', '0.40'],
            ['CDL3WHITESOLDIERS',
                '* Three Advancing White Soldiers *', 'High R2BU', '-0.001', '0.333'],
            ['CDLABANDONEDBABY', '* Abandoned Baby *', 'High reversal', '-0.046)', '0.318'],
            ['CDLADVANCEBLOCK', 'Advance Block', '', '0.142', '0.381'],
            # ['CDLBELTHOLD' , 'Belt-hold', '','0.037', '0.346'],            [
            ['CDLBREAKAWAY', 'Breakaway',
                'High Over(Sold/bought) 5 day use as conf', '0.109', '0.37'],
            ['CDLCLOSINGMARUBOZU', 'Closing Marubozu', 'Rare High confirmation', '-0.047', '0.318'],
            ['CDLCONCEALBABYSWALL', '* Concealing Baby Swallow *', 'Medium Rare R2BU', '0.50', '0.50'],
            ['CDLCOUNTERATTACK', 'Counterattack', 'Low Reversal w conf', '0', '0'],
            ['CDLDARKCLOUDCOVER', 'Dark Cloud Cover', '', '0.061', '0.354'],
            # ['CDLDOJI','Doji','','',''],
            ['CDLDOJISTAR', 'Doji Star', '', '0.238', '0.413'],
            # ['CDLDRAGONFLYDOJI', 'Dragonfly Doji', '', '0.054', '0.351'],
            ['CDLENGULFING', 'Engulfing Pattern', 'Low Reversal', '0.104', '0.368'],
            ['CDLEVENINGDOJISTAR', 'Evening Doji Star', 'High R2BE', '', ''],
            ['CDLEVENINGSTAR', '* Evening Star *', 'Rare High R2BE', '0.006', '0.335'],
            # ['CDLGAPSIDESIDEWHITE', 'Up/Down-gap side-by-side white lines', '', '0.013', '0.338'],
            ['CDLGRAVESTONEDOJI', 'Gravestone Doji', '', '0.196', '0.399'],
            ['CDLHAMMER', 'Hammer', 'Medium R2BU', '0.225', '0.408'],
            ['CDLHANGINGMAN', 'Hanging Man', 'Medium R2BE', '0.075', '0.358'],
            ['CDLHARAMI', 'Harami Pattern', '', '0.219', '0.406'],
            ['CDLHARAMICROSS', 'Harami Cross Pattern', '', '0.207', '0.402'],
            ['CDLHIGHWAVE', 'High-Wave Candle', '', '0.263', '0.421'],
            ['CDLHIKKAKE', 'Hikkake Pattern', '', '0.11', '0.371'],
            ['CDLHIKKAKEMOD', 'Modified Hikkake Pattern', '', '0.14', '0.381'],
            ['CDLHOMINGPIGEON', 'Homing Pigeon', '', '0.344', '0.448'],
            ['CDLIDENTICAL3CROWS', '* Identical Three Crows *', 'High R2BE', '-0.078', '0.307'],
            # ['CDLINNECK', 'In-Neck Pattern', 'Low Continuation', '0.047', '0.349'],
            ['CDLINVERTEDHAMMER', 'Inverted Hammer', 'Medium R2BU', '0.182', '0.394'],
            # ['CDLKICKING', 'Kicking', '', '-0.11', '0.294'],
            # ['CDLKICKINGBYLENGTH','Kicking', 'bull/bear determined by the longer marubozu', '-0.117', '0.294'],
            ['CDLLADDERBOTTOM', 'Ladder Bottom', '', '-0.147', '0.382'],
            # ['CDLLONGLEGGEDDOJI', 'Long Legged Doji', '', '', ''],
            # ['CDLMARUBOZU', 'Marubozu', '', '-0.085', '0.305'],
            ['CDLMATCHINGLOW', 'Matching Low', '', '0.261', '0.42'],
            # ['CDLMATHOLD', 'Mat Hold', '','-0.40', '0.20'],
            ['CDLMORNINGDOJISTAR', 'Morning Doji Star', '', '0', '0'],
            ['CDLMORNINGSTAR', 'Morning Star', '', '0.152', '0.384'],
            # ['CDLONNECK', 'On-Neck Pattern', '', '0.015', '0.338'],
            ['CDLPIERCING', 'Piercing Pattern', '', '0.185', '0.395'],
            ['CDLRICKSHAWMAN', 'Rickshaw Man', '', '0.304', '0.435'],
            ['CDLRISEFALL3METHODS', 'Rising/Falling Three Methods', '', '0.088', '0.363'],
            # ['CDLSEPARATINGLINES', 'Separating Lines', '', '-0.049', '0.317'],
            ['CDLSHOOTINGSTAR', 'Shooting Star', '', '0.135', '0.378'],
            # ['CDLSHORTLINE', 'Short Line Candle', '', '', ''],
            ['CDLSPINNINGTOP', 'Spinning Top', '', '0.271', '0.424'],
            # ['CDLSTALLEDPATTERN', 'Stalled Pattern', '', '', ''],
            ['CDLSTICKSANDWICH', 'Stick Sandwich', '', '0.273', '0.424'],
            # ['CDLTAKURI', 'Takuri (Dragonfly Doji with very long lower shadow)','', '0.038', '0.346'],
            ['CDLTASUKIGAP', 'Tasuki Gap', '', '0.17', '0.39'],
            # ['CDLTHRUSTING', 'Thrusting Pattern', '', '0.051', '0.35'],
            # ['CDLTRISTAR', 'Tristar Pattern', '', '0.032', '0.344'],
            ['CDLUNIQUE3RIVER', 'Unique 3 River', '', '0.206', '0.402'],
            ['CDLUPSIDEGAP2CROWS', 'Upside Gap Two Crows', '', '0.158', '0.386'],
            ['CDLXSIDEGAP3METHODS', 'Upside/Downside Gap Three Methods', '', '0.133', '0.378']
        ]), columns=['cod', 'desc', 'impact', 'roi', 'successrate'])

    def dailyScan(self):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrBacktrader import rrBacktrader as rrbt
        self.bt = rrbt()
        stocks = self.db.getStocks()
        # for index, stock in tqdm(stocks.iterrows(), desc="  Getting Historic Data", unit="Stock", ascii=False, ncols=120, leave=False):
        report = pd.DataFrame(columns=['stock', 'pattern', 'date', 'signal'])
        for index, stock in stocks.iterrows():
            try:
                hd = self.bt.getHistoricData(stock['ticker'])
                for index, cod in self.patterns.iterrows():
                    func = getattr(talib, cod['cod'])
                    result = func(hd['open'], hd['high'], hd['low'], hd['close'])
                    last = result.tail(3)
                    for index, entryCode in last.items():
                        if entryCode != 0:
                            if entryCode == 200:
                                entry = "Bullish with Confirmation"
                            elif entryCode == 100:
                                entry = "Bullish"
                            elif entryCode == -100:
                                entry = "Bearish"
                            elif entryCode == -200:
                                entry = "Bearish with Confirmation"
                            report = report.append(
                                {'stock': stock['ticker'], 'pattern': cod['desc'], 'date': index, 'signal': entry, 'impact': cod['impact'], 'roi': cod['roi'], 'successrate': cod['successrate']}, ignore_index=True)
            except Exception as e:
                self.log.logger.warning("Problem daily scanner")
                self.log.logger.warning(e)
        report = report.sort_values(['stock', 'date', 'roi'], ascending=(True, True, True))
        return report

    def communicateScan(self):
        import datetime
        from rrlib.rrTelegram import rrTelegram
        from rrlib.rrIFTTT import rrIFTTT

        ds = rrDailyScan().dailyScan()
        for index, stock in self.db.getStocks().iterrows():
            stk = str(stock['ticker'])
            self.log.logger.info("    Daily Scan for: " + stk)
            try:
                for index, event in ds[ds.stock == stk].iterrows():
                    self.log.logger.info("      event: " + event['date'].strftime("%d/%m")+", Pattern: "+str(event['pattern']) +
                                         ", signal: " +
                                         str(event['signal']) + ", ROI "+str(event['roi'])+", success rate " + str(event['successrate'])+". "+str(event['impact']))
                    if(datetime.datetime.now().isoweekday() == 1):
                        daydelta = 4
                    elif datetime.datetime.now().isoweekday() == 7:
                        daydelta = 3
                    else:
                        daydelta = 2
                    if float(event['roi']) > 0.1 and float(event['successrate']) > 0.2 and (datetime.datetime.now()-datetime.timedelta(days=3)) < event['date']:
                        self.db.updateServerRun(prospectsFound="Yes")
                        report = {}
                        report["value1"] = "Daily Scanner: Prospect Found: Stock:"+stk+" event:" + \
                            event['date'].strftime("%d/%m")+" Pattern:" + str(event['pattern'])
                        report["value2"] = "Signal:" + str(event['signal'])+" Entry:" + \
                            "" + ", Stop Loss:"+""+", Take Profit:"+""
                        report["value3"] = "ROI:" + str(event['roi'])+", Success Rate:" + str(
                            event['successrate'])+", Impact:"+str(event['impact'])
                        try:
                            if(float(event['roi']) > 0.2) and (datetime.datetime.now()-datetime.timedelta(days=daydelta)) < event['date']:
                                rrIFTTT().send(report)
                                rrTelegram().sendMessage(
                                    str(report["value1"])+" | "+str(report["value2"])+" | "+str(report["value3"]))
                                rrTelegram().sendImage("https://charts2.finviz.com/chart.ashx?t="+stk+"&ty=c&ta=1&p=d&s=l")
                        except Exception as e:
                            self.log.logger.error(
                                "     Daily scan communications error")
                            self.log.logger.error(e)
            except Exception as e:
                self.log.logger.error(e)
