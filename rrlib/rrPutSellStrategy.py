#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 04 2021
robotRay server v1.0
@author: camilorojas

Put Sell Strategy module (former Thinker module)

Process for module v1
1. Evaluate for list of stocks intraday lows greater than 4.5% decrease in price
2. Retreive last price and price range for elegible stocks
3. Evaluate pricing opportunities for these stocks with enough volume and open positions
4. Evaluate best month scenario to recommend
5. Communicate to Camilor if there are prospects above the limit kpi's

Active Evaluator module
1. Save all recommended prospects with decision information
2. Evaluate if sell premium has been captured
3. Communicate to Camilor to close positions

Passive Evaluator module
Batch nature for evaluation of alerted positions

"""

import sys
import os
import datetime
from tqdm import tqdm
import pandas as pd


class rrPutSellStrategy:
    def __init__(self):
        # starting common services
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        # starting logging
        from rrlib.rrLogger import logger
        self.log = logger()
        # starting backend services
        from rrlib.rrDb import rrDbManager
        self.db = rrDbManager()
        # portfolio startup
        from rrlib.rrPortfolio import rrPortfolio
        self.portfolio = rrPortfolio()
        # starting ini parameters
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        # daily decrease green if % stock dtd growth < -4.5%, -4.5% < yellow < 2%, red > 2%
        self.dayPriceChgGreen = config.get('sellputstrategy', 'dayPriceChgGreen')
        self.dayPriceChgRed = config['sellputstrategy']['dayPriceChgRed']
        # expected minimum monthly premium for holding the option 1%
        self.monthlyPremium = self.portfolio.monthlyPremium
        # sma200 below 0 is red, <0.1 yellow, > 0.1 green
        self.smaGreen = config['sellputstrategy']['smaGreen']
        self.smaRed = config['sellputstrategy']['smaRed']
        # sales growth quarter to quarter
        self.salesGrowthGreen = config['sellputstrategy']['salesGrowthGreen']
        self.salesGrowthRed = config['sellputstrategy']['salesGrowthRed']
        # retreive R
        self.R = self.portfolio.R
        self.availableFunds = self.portfolio.funds
        # Intraday kpi green and red
        self.IntradayKPIGreen = config['sellputstrategy']['IntradayKPIGreen']
        self.IntradayKPIRed = config['sellputstrategy']['IntradayKPIRed']
        # Get number of days to BTC on Options
        self.BTCdays = config['sellputstrategy']['BTCdays']
        # Get option expected price flexiblity to ask limit
        self.ExpPrice2Ask = config['sellputstrategy']['ExpPrice2Ask']
        # is telegram bot enabled for commands
        self.startbot = config.get('telegram', 'startbot')
        # Get verbose option boolean
        self.verbose = config['sellputstrategy']['verbose']
        self.log.logger.debug("  Put Sell Strategy module starting.  ")

    def evaluateProspects(self):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrDb import IntradayStockData
        from rrlib.rrDb import OptionData
        from rrlib.rrDb import StockData

        # print debug init parameters
        if(self.verbose == "Yes"):
            self.log.logger.info(
                "     105. Put Sell Strategy operational parameters: Day Percentage Change for Green day:" +
                str(float(self.dayPriceChgGreen)*100)
                + "%, for Red Day:" + str(float(self.dayPriceChgRed)*100)+"%")
            self.log.logger.info("     Monthly Expected Premium:" + str(float(self.monthlyPremium)*100)
                                 + "%, Simple Moving Average 200 for Green Day:" +
                                 str(float(self.smaGreen)*100) +
                                 "%, for Red Day:" + str(float(self.smaRed*100))+"%")
            self.log.logger.info("     Available funds in portfolio: USD$" +
                                 str(self.availableFunds)+", R (risk money per trade):USD$" + self.R)

        try:
            for stock in tqdm(IntradayStockData.select(), desc="Getting KPI's of Stock Data:", unit="Stock", ascii=False, ncols=120, leave=False):
                strike = StockData.select(StockData.strike).where(
                    StockData.stock == stock.stock).order_by(StockData.id.desc()).get().strike
                if float(stock.pctChange) < float(self.dayPriceChgGreen) and float(stock.kpi) > float(self.IntradayKPIGreen):
                    try:
                        higherOptionData = OptionData.select().where(
                            (OptionData.stock == stock.stock) & (OptionData.strike == strike) &
                            (OptionData.timestamp > (datetime.datetime.now()-datetime.timedelta(days=4)))).order_by(OptionData.kpi.desc()).get()
                        if float(higherOptionData.price) > float(higherOptionData.expectedPremium):
                            price = higherOptionData.price
                        else:
                            price = higherOptionData.expectedPremium
                        # found a prospect
                        if float(price) < float(higherOptionData.ask)*float(self.ExpPrice2Ask) and float(higherOptionData.contracts) > 0:
                            self.log.logger.info(
                                "     Put Sell Strategy found a prospect with green day decline and also green KPI, STO Puts for: "+stock.stock)
                            self.log.logger.info(self.prospectFormatter(stock.stock, str(higherOptionData.expireDate), strike, price,
                                                                        higherOptionData.contracts,
                                                                        higherOptionData.bid, higherOptionData.ask, higherOptionData.expectedPremium,
                                                                        higherOptionData.Rpotential))
                            # save prospect db for communication
                            self.db.saveProspect(stock.stock, strike, higherOptionData.expireDate, price, higherOptionData.contracts,
                                                 higherOptionData.stockOwnership, higherOptionData.Rpotential,
                                                 kpi=higherOptionData.kpi, color="green")
                    except OptionData.DoesNotExist:
                        tqdm.write(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
                                   + " - rrLog - " +
                                   "INFO -       Green Potential day decline, but no option data for: "+stock.stock +
                                   " with strike:"+strike + ", in the last 4 days")
                # Yellow day decline
                elif float(stock.pctChange) < float(self.dayPriceChgRed) and float(stock.kpi) > float(self.IntradayKPIGreen):
                    try:
                        higherOptionData = OptionData.select().where(
                            (OptionData.stock == stock.stock) & (OptionData.strike == strike) &
                            (OptionData.timestamp > (datetime.datetime.now()-datetime.timedelta(days=4)))).order_by(OptionData.kpi.desc()).get()
                        if float(higherOptionData.price) > float(higherOptionData.expectedPremium):
                            price = higherOptionData.price
                        else:
                            price = higherOptionData.expectedPremium
                        # found a prospect
                        if float(price) < float(higherOptionData.ask)*float(self.ExpPrice2Ask) and float(higherOptionData.contracts) > 0:
                            self.log.logger.info(
                                "     Put Sell Strategy found a prospect with yellow day decline and also green KPI, STO Puts for: "+stock.stock)
                            self.log.logger.info(self.prospectFormatter(stock.stock, str(higherOptionData.expireDate), strike, price,
                                                                        higherOptionData.contracts,
                                                                        higherOptionData.bid, higherOptionData.ask, higherOptionData.expectedPremium,
                                                                        higherOptionData.Rpotential))
                            self.db.saveProspect(stock.stock, strike, higherOptionData.expireDate, price, higherOptionData.contracts,
                                                 higherOptionData.stockOwnership, higherOptionData.Rpotential,
                                                 kpi=higherOptionData.kpi, color="yellow")
                    except OptionData.DoesNotExist:
                        tqdm.write(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
                                   + " - rrLog - " +
                                   "INFO -        Yellow Potential day decline, but no option data for: "+stock.stock +
                                   " with strike:"+strike + ", in the last 4 days")

        except Exception as e:
            self.log.logger.error("     Put Sell Strategy evaluation error")
            self.log.logger.error(e)

    def prospectFormatter(self, stock="STOCK", expireDate="YYYY-MM-DD", strike="100", price="1", contracts="1",
                          bid="1.1", ask="1.1", expectedPremium="1", Rpotential="1.1"):
        message = ""
        try:
            message = "\n\n" + "     --------------PROSPECT DETAILS-------------------\n" + "     STO " + \
                stock + " " + expireDate + "P" + strike + " price:" + str(round(float(price), 2))+"\n" + "     Best month is: " + expireDate + \
                ", strike "+strike + ", price " + str(round(float(price), 2)) + ", quantity " + contracts + ", current range is \n" + "     Bid: " + \
                str(round(float(bid), 2)) + " and Ask: " + str(round(float(ask), 2)) + " min premium expected is: " + \
                str(round(float(expectedPremium), 2)) + " and RPotential is: " + str(round(float(Rpotential), 2))+"\n" + \
                "     BTC when price reaches either Price: " + str(round(float(price)/2, 2)) + "\n" + \
                "     --------------PROSPECT DETAILS-------------------\n"
        except Exception as e:
            self.log.logger.error(
                "     Put Sell Strategy prospect formatter error")
            self.log.logger.error(e)
        return message

    def communicateProspects(self):
        import datetime
        from rrlib.rrTelegram import rrTelegram
        from rrlib.rrIFTTT import rrIFTTT
        from rrlib.rrDb import ProspectData as pd
        try:
            for prospect in pd.select().where(pd.STOcomm.is_null()):
                report = {}
                report["value1"] = "Put Sell Strategy: Prospect Found: Stock:"+prospect.stock+" Strike:" + \
                    prospect.strike+" Expiration Date:" + str(prospect.expireDate)
                report["value2"] = "Contracts:" + prospect.contracts+" Price:" + str(round(float(
                    prospect.price), 3)) + " RPotential:"+str(round(float(prospect.Rpotential), 2))
                report["value3"] = "Stock ownership:" +\
                    prospect.stockOwnership+" Color:"+prospect.color
                self.log.logger.debug(
                    "    Communicator , invoking with these parameters "+str(report))
                self.db.updateServerRun(prospectsFound="Yes")
                try:
                    r = rrIFTTT().send(report)
                    rrTelegram().sendMessage(
                        str(report["value1"])+" | "+str(report["value2"])+" | "+str(report["value3"]))
                    print("Enviado por IFTT:"+str(r))
                    if str(r) == "<Response [200]>":
                        pd.update({pd.STOcomm: datetime.datetime.today()}).where((pd.stock == prospect.stock) & (
                            pd.strike == prospect.strike) & (pd.expireDate == prospect.expireDate)).execute()

                except Exception as e:
                    self.log.logger.error(
                        "     Put Sell Strategy prospect IFTTT error")
                    self.log.logger.error(e)
        except Exception as e:
            self.log.logger.error(
                "     Put Sell Strategy prospect communicator error")
            self.log.logger.error(e)

    def communicateClosing(self):
        import datetime
        from rrlib.rrTelegram import rrTelegram
        from rrlib.rrIFTTT import rrIFTTT
        from rrlib.rrDb import ProspectData as pd
        try:
            for prospect in pd.select().where(pd.BTCcomm.is_null()):
                if ((float(prospect.price)/2 > float(prospect.currentPrice)) or
                        (float((prospect.expireDate-datetime.date.today()).days) < float(self.BTCdays))):
                    pnl = str(round(float(prospect.contracts) *
                                    (float(prospect.price)-float(prospect.currentPrice))*100-float(prospect.contracts)*2, 2))
                    report = {}
                    report["value1"] = "Time to close the contract<br>Stock:"+prospect.stock +\
                        " Strike:" + prospect.strike +\
                        " Expiration Date:" + str(prospect.expireDate)
                    report["value2"] = "Contracts:" + prospect.contracts+" Closing Price:" +\
                        str(round(float(prospect.currentPrice), 3)) +\
                        " PNL for this oppty:" + pnl
                    report["value3"] = "Stock ownership:" +\
                        prospect.stockOwnership+" Color:"+prospect.color
                    self.log.logger.debug(
                        "    Communicator, invoking with these parameters " + str(report))
                    self.db.updateServerRun(pnl=pnl)
                    try:
                        r = rrIFTTT().send(report)
                        if (self.startbot == "Yes"):
                            rrTelegram().sendMessage(
                                str(report["value1"])+" | "+str(report["value2"])+" | "+str(report["value3"]))
                        if str(r) == "<Response [200]>":
                            pd.update({pd.BTCcomm: datetime.datetime.today(), pd.pnl: pnl}).where((pd.stock == prospect.stock) &
                                                                                                  (pd.strike == prospect.strike) &
                                                                                                  (pd.expireDate == prospect.expireDate)).execute()

                    except Exception as e:
                        self.log.logger.error(
                            "     Put Sell Strategy comm closing IFTTT error")
                        self.log.logger.error(e)
        except Exception as e:
            self.log.logger.error(
                "     Put Sell Strategy communicator closing error")
            self.log.logger.error(e)

    def updatePricingProspects(self):
        from rrlib.rrDb import ProspectData as pd
        from rrlib.rrDb import OptionData as od
        try:
            for pt in pd.select().where(pd.BTCcomm.is_null()):
                self.log.logger.debug("    Put Sell Strategy updating prices for: " + str(pt))
                currentPrice = od.select(od.price).where((od.stock == pt.stock) & (
                    od.strike == pt.strike) & (od.expireDate == pt.expireDate)).get().price
                pnl = str(round(float(pt.contracts) *
                                (float(pt.price)-float(pt.currentPrice))*100-float(pt.contracts)*2, 2))
                self.log.logger.debug("    Put Sell Strategy updating prices for: " + pt.stock+" current price:"+currentPrice +
                                      " old price:"+pt.currentPrice)
                pd.update({pd.currentPrice: currentPrice, pd.pnl: pnl}).where((pd.stock == pt.stock) &
                                                                              (pd.strike == pt.strike) &
                                                                              (pd.expireDate == pt.expireDate)).execute()
        except Exception as e:
            self.log.logger.error(
                "     Put Sell Strategy pricing update error")
            self.log.logger.error(e)

    def printAllProspects(self):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrDb import ProspectData as pdata
        df = pd.DataFrame(list(pdata.select().order_by(pdata.pnl.desc()).dicts()))
        return df

    def printOpenProspects(self):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrDb import ProspectData as pdata
        df = pd.DataFrame(list(pdata.select().where(
            pdata.BTCcomm.is_null()).order_by(pdata.pnl.desc()).dicts()))
        return df

    def printClosedProspects(self):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrDb import ProspectData as pdata
        df = pd.DataFrame(list(pdata.select().where(
            pdata.BTCcomm.is_null(False)).order_by(pdata.pnl.desc()).dicts()))
        return df

    def sendDailyReport(self):
        from rrlib.rrDb import ProspectData as pd
        from rrlib.rrTelegram import rrTelegram
        from rrlib.rrIFTTT import rrIFTTT
        pnlClosed = 0
        numClosed = 0
        pnlOpen = 0
        numOpen = 0
        try:
            for pt in pd.select().where(pd.BTCcomm.is_null(False)):
                pnlClosed = pnlClosed + float(pt.pnl)
                numClosed = numClosed + 1
            for pt in pd.select().where(pd.BTCcomm.is_null()):
                pnlOpen = pnlOpen + float(pt.pnl)
                numOpen = numOpen + 1

            report = {}
            report["value1"] = "PNL Closed: $" +\
                str(round(pnlClosed, 2))+" with "+str(numClosed)+" prospects"
            report["value2"] = "PNL Open:   $" +\
                str(round(pnlOpen, 2))+" with "+str(numOpen)+" prospects"
            report["value3"] = "PNL Total:  $"+str(
                round(pnlClosed + pnlOpen, 2))+" with "+str(numClosed+numOpen)+" prospects"
            self.log.logger.info("\n\n    -------------------DAILY REPORT-------------------\n    "+str(
                report["value1"])+"\n    "+str(report["value2"])+"\n    "+str(report["value3"]) +
                "\n    ------------------DAILY REPORT-------------------\n")
            try:
                r = rrIFTTT().send(report)
                rrTelegram().sendMessage(
                    str(report["value1"])+" | "+str(report["value2"])+" | "+str(report["value3"]))
                if str(r) == "<Response [200]>":
                    pass
            except Exception as e:
                self.log.logger.error(
                    "     Put Sell Strategy daily report communication error")
                self.log.logger.error(e)
        except Exception as e:
            self.log.logger.error(
                "     Put Sell Strategy sending daily report error")
            self.log.logger.error(e)
