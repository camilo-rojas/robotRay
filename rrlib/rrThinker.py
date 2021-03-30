#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 05 2019

@author: camilorojas

Thinker module

Process for thinker module v1
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


class thinker:
    def __init__(self):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrLogger import logger
        from rrlib.rrDb import rrDbManager
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        self.log = logger()
        self.log.logger.debug("  Thinker module starting.  ")
        self.db = rrDbManager()
        # daily decrease green if % stock dtd growth < -4.5%, -4.5% < yellow < 2%, red > 2%
        self.dayPriceChgGreen = config.get('thinker', 'dayPriceChgGreen')
        self.dayPriceChgRed = config['thinker']['dayPriceChgRed']
        # expected minimum monthly premium for holding the option 1%
        self.monthlyPremium = config['thinker']['monthlyPremium']
        # sma200 below 0 is red, <0.1 yellow, > 0.1 green
        self.smaGreen = config['thinker']['smaGreen']
        self.smaRed = config['thinker']['smaRed']
        # sales growth quarter to quarter
        self.salesGrowthGreen = config['thinker']['salesGrowthGreen']
        self.salesGrowthRed = config['thinker']['salesGrowthRed']
        # retreive R
        self.R = config['thinker']['R']
        # Intraday kpi green and red
        self.IntradayKPIGreen = config['thinker']['IntradayKPIGreen']
        self.IntradayKPIRed = config['thinker']['IntradayKPIRed']
        # Get IFTTT key for future use on notifications
        self.IFTTT = config['ifttt']['key']
        # Get number of days to BTC on Options
        self.BTCdays = config['thinker']['BTCdays']
        # Get option expected price flexiblity to ask limit
        self.ExpPrice2Ask = config['thinker']['ExpPrice2Ask']
        # print debug init parameters
        self.log.logger.debug(
            "     Thinker operational parameters: DPCGreen:" + self.dayPriceChgGreen
            + ", DPCRed:" + self.dayPriceChgRed + ", MonthPrem:" + self.monthlyPremium
            + ", SMAGreen:" + self.smaGreen + ", SMARed:" + self.smaRed + ", R:" + self.R)

    def evaluateProspects(self):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrDb import IntradayStockData
        from rrlib.rrDb import OptionData
        from rrlib.rrDb import StockData

        try:
            for stock in IntradayStockData.select():
                self.log.logger.debug("     Thinker:" + str(float(stock.kpi)) + " "
                                      + str(float(self.IntradayKPIGreen)) + " "
                                      + str(float(stock.pctChange)))
                # Find the strike price
                strike = StockData.select(StockData.strike).where(
                    StockData.stock == stock.stock).get().strike
                # print(str(stock.pctChange < self.dayPriceChgGreen) +
                #      " "+str(stock.kpi > self.IntradayKPIGreen))
                # Green day decline
                if float(stock.pctChange) < float(self.dayPriceChgGreen) and float(stock.kpi) > float(self.IntradayKPIGreen):
                    higherOptionData = OptionData.select().where(
                        (OptionData.stock == stock.stock) & (OptionData.strike == strike)).order_by(OptionData.kpi.desc()).get()
                    if float(higherOptionData.price) > float(higherOptionData.expectedPremium):
                        price = higherOptionData.price
                    else:
                        price = higherOptionData.expectedPremium
                    # found a prospect
                    if float(price) < float(higherOptionData.ask)*float(self.ExpPrice2Ask):
                        self.log.logger.info(
                            "     Thinker found a prospect with green day decline and also green KPI, STO Puts for: "+stock.stock)
                        self.log.logger.info(self.prospectFormatter(stock.stock, str(higherOptionData.expireDate), strike, price,
                                                                    higherOptionData.contracts,
                                                                    higherOptionData.bid, higherOptionData.ask, higherOptionData.expectedPremium,
                                                                    higherOptionData.Rpotential))
                        # save prospect db for communication
                        self.db.saveProspect(stock.stock, strike, higherOptionData.expireDate, price, higherOptionData.contracts,
                                             higherOptionData.stockOwnership, higherOptionData.Rpotential, kpi=higherOptionData.kpi, color="green")
                # Yellow day decline
                elif float(stock.pctChange) < float(self.dayPriceChgRed) and float(stock.kpi) > float(self.IntradayKPIGreen):
                    higherOptionData = OptionData.select().where(
                        (OptionData.stock == stock.stock) & (OptionData.strike == strike)).order_by(OptionData.kpi.desc()).get()
                    if float(higherOptionData.price) > float(higherOptionData.expectedPremium):
                        price = higherOptionData.price
                    else:
                        price = higherOptionData.expectedPremium
                    # found a prospect
                    if float(price) < float(higherOptionData.ask)*float(self.ExpPrice2Ask):
                        self.log.logger.info(
                            "     Thinker found a prospect with yellow day decline and also green KPI, STO Puts for: "+stock.stock)
                        self.log.logger.info(self.prospectFormatter(stock.stock, str(higherOptionData.expireDate), strike, price,
                                                                    higherOptionData.contracts,
                                                                    higherOptionData.bid, higherOptionData.ask, higherOptionData.expectedPremium,
                                                                    higherOptionData.Rpotential))
                        self.db.saveProspect(stock.stock, strike, higherOptionData.expireDate, price, higherOptionData.contracts,
                                             higherOptionData.stockOwnership, higherOptionData.Rpotential, kpi=higherOptionData.kpi, color="yellow")
        except Exception:
            self.log.logger.error(
                "     Thinker evaluation error" + Exception.with_traceback)

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
        except Exception:
            self.log.logger.error(
                "     Thinker prospect formatter error" + Exception.with_traceback)
        return message

    def communicateProspects(self):
        import requests
        import datetime
        from rrlib.rrDb import ProspectData as pd
        try:
            for prospect in pd.select().where(pd.STOcomm.is_null()):
                report = {}
                report["value1"] = "Stock:"+prospect.stock+" Strike:" + \
                    prospect.strike+" Expiration Date:" + \
                    str(prospect.expireDate)
                report["value2"] = "Contracts:" + prospect.contracts+" Price:" + str(round(float(
                    prospect.price), 3)) + " RPotential:"+str(round(float(prospect.Rpotential), 2))
                report["value3"] = "Stock ownership:" + \
                    prospect.stockOwnership+" Color:"+prospect.color
                self.log.logger.debug(
                    "    Communicator , invoking with these parameters "+str(report))
                try:
                    r = requests.post(
                        "https://maker.ifttt.com/trigger/robotray_sto_comm/with/key/"+self.IFTTT, data=report)
                    if r.status_code == 200:
                        pd.update({pd.STOcomm: datetime.datetime.today()}).where((pd.stock == prospect.stock) &
                                                                                 (pd.strike == prospect.strike) &
                                                                                 (pd.expireDate == prospect.expireDate)).execute()

                except Exception:
                    self.log.logger.error(
                        "     Thinker prospect IFTTT error" + Exception.with_traceback)
        except Exception:
            self.log.logger.error(
                "     Thinker prospect communicator error" + Exception.with_traceback)

    def communicateClosing(self):
        import requests
        import datetime
        from rrlib.rrDb import ProspectData as pd
        try:
            for prospect in pd.select().where(pd.BTCcomm.is_null()):
                if ((float(prospect.price)/2 > float(prospect.currentPrice)) or
                        (float((prospect.expireDate-datetime.date.today()).days) < float(self.BTCdays))):
                    pnl = str(round(float(prospect.contracts) *
                                    (float(prospect.price)-float(prospect.currentPrice))*100-float(prospect.contracts)*2, 2))
                    report = {}
                    report["value1"] = "Time to close the contract<br>Stock:"+prospect.stock + \
                        " Strike:" + prospect.strike + \
                        " Expiration Date:" + str(prospect.expireDate)
                    report["value2"] = "Contracts:" + prospect.contracts+" Closing Price:" + \
                        str(round(float(prospect.currentPrice), 3)) + \
                        " PNL for this oppty:" + pnl
                    report["value3"] = "Stock ownership:" + \
                        prospect.stockOwnership+" Color:"+prospect.color
                    self.log.logger.debug(
                        "    Communicator, invoking with these parameters " + str(report))
                    try:
                        r = requests.post(
                            "https://maker.ifttt.com/trigger/robotray_btc_comm/with/key/"+self.IFTTT, data=report)
                        if r.status_code == 200:
                            pd.update({pd.BTCcomm: datetime.datetime.today(), pd.pnl: pnl}).where((pd.stock == prospect.stock) &
                                                                                                  (pd.strike == prospect.strike) &
                                                                                                  (pd.expireDate == prospect.expireDate)).execute()

                    except Exception:
                        self.log.logger.error(
                            "     Thinker comm closing IFTTT error" + Exception.with_traceback)
        except Exception:
            self.log.logger.error(
                "     Thinker communicator closing error" + Exception.with_traceback)

    def updatePricingProspects(self):
        from rrlib.rrDb import ProspectData as pd
        from rrlib.rrDb import OptionData as od
        try:
            for pt in pd.select().where(pd.BTCcomm.is_null()):
                currentPrice = od.select(od.price).where((od.stock == pt.stock) & (
                    od.strike == pt.strike) & (od.expireDate == pt.expireDate)).get().price
                pnl = str(round(float(pt.contracts) *
                                (float(pt.price)-float(pt.currentPrice))*100-float(pt.contracts)*2, 2))
                self.log.logger.debug("    Thinker updating prices for: " + pt.stock+" current price:"+currentPrice +
                                      " old price:"+pt.currentPrice)
                pd.update({pd.currentPrice: currentPrice, pd.pnl: pnl}).where((pd.stock == pt.stock) &
                                                                              (pd.strike == pt.strike) &
                                                                              (pd.expireDate == pt.expireDate)).execute()
        except Exception:
            self.log.logger.error(
                "     Thinker pricing update error" + Exception.with_traceback)

    def sendDailyReport(self):
        from rrlib.rrDb import ProspectData as pd
        import requests
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
            report["value1"] = "PNL Closed: $" + \
                str(round(pnlClosed, 2))+" with "+str(numClosed)+" prospects"
            report["value2"] = "PNL Open:   $" + \
                str(round(pnlOpen, 2))+" with "+str(numOpen)+" prospects"
            report["value3"] = "PNL Total:  $"+str(
                round(pnlClosed + pnlOpen, 2))+" with "+str(numClosed+numOpen)+" prospects"
            self.log.logger.info("\n\n    -------------------DAILY REPORT-------------------\n    "+str(
                report["value1"])+"\n    "+str(report["value2"])+"\n    "+str(report["value3"]) +
                "\n    ------------------DAILY REPORT-------------------\n")
            try:
                r = requests.post(
                    "https://maker.ifttt.com/trigger/robotray_dailyreport/with/key/"+self.IFTTT, data=report)
                if r.status_code == 200:
                    pass
            except Exception:
                self.log.logger.error(
                    "     Thinker daily report IFTTT error" + Exception.with_traceback)
        except Exception:
            self.log.logger.error(
                "     Thinker sending daily report error" + Exception.with_traceback)