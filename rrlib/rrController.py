# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 05 2019
robotRay server v1.0
@author: camilorojas

Controller class file that coordinates channel requests and executes with backend commands
Initially attending Telegram service.   Future will connect server interaction
"""

import threading
import sys
import os
import configparser
import datetime
from rrlib.rrPutSellStrategy import rrPutSellStrategy
from rrlib.rrGoldenStrategy import rrGoldenStrategy
from rrlib.rrBacktrader import rrBacktrader
from rrlib.rrDailyScan import rrDailyScan


class rrController():
    def __init__(self, *args, **kwargs):
        # starting common services
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        # starting logging service
        from rrlib.rrLogger import logger
        self.log = logger()
        # starting backend services
        from rrlib.rrDb import rrDbManager
        self.db = rrDbManager()
        self.bt = rrBacktrader()
        self.sellp = rrPutSellStrategy()
        self.rrGoldenStrategy = rrGoldenStrategy()
        # starting ini parameters
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        # run outside trading hours
        self.oth = config.get("debug", "oth")
        self.log.logger.debug("Initialization finished robotRay controller")
        # controller runtime variables
        self.runCycle = 0

    def botcommand(self, command=""):
        response = []
        command = command.lower()
        if (command == "intro" or command == "about"):
            response.append("")
            response.append("RobotRay by Camilo Rojas")
        elif(command == "help"):
            response.append("")
            response.append(
                "RobotRay Help Menu - for Telegram")
            response.append(
                "General Commands: help, status, source, jobs, intro, about")
            response.append(
                "Stock Data info commands: printstocks, printintra")
            response.append("Option Data info commands: printoptions")
            response.append(
                "Run prospect info: printallp, printopenp, printclosedp, sendp")
            response.append(
                "Statistics for bot operations: report, reporty, reportytd, reportsm, reportw")
        elif (command == "source"):
            response.append("")
            if (self.db.getSource() == "public"):
                response.append("Current data fetched from: Finviz & Yahoo")
            elif (self.db.getSource() == "ib"):
                response.append("Current data fetched from: Interactive Brokers")
            else:
                response.append(self.db.getSource())
        elif (command == "printstocks"):
            response.append("")
            response.append("Stocks being tracked")
            response.append(self.db.printStocks())
        elif (command == "printintra"):
            response.append("")
            response.append("Stocks current intraday data")
            response.append(self.db.printIntradayStocks())
        elif (command == "printoptions"):
            response.append("")
            response.append("Options data")
            response.append(self.db.printOptions())
        elif (command == "printopenp"):
            response.append("")
            response.append("Open Prospect data")
            response.append(self.sellp.printOpenProspects())
        elif (command == "printclosedp"):
            response.append("")
            response.append("Closed Prospect data")
            response.append(self.sellp.printClosedProspects())
        elif (command == "printallp"):
            response.append("")
            response.append("All Prospect data sorted by PNL")
            response.append(self.sellp.printAllProspects())
        elif(command == "sendp"):
            response.append("")
            response.append("Sent daily report of prospects")
            self.sellp.sendDailyReport()
        elif(command == "getstockdata"):
            response.append("db.getStockData")
            response.append("Getting stock data manually")
        elif(command == "getintra"):
            response.append("db.getIntradayData")
            response.append("Getting stock intraday data manually")
        elif(command == "getoptiondata"):
            response.append("db.getOptionData")
            response.append("Getting stock option data manually")
        elif(command == "status"):
            response.append("")
            response.append("Status report RobotRay.")
            if (self.db.getSource() == "public"):
                response.append("Current data fetched from: Finviz & Yahoo")
            elif (self.db.getSource() == "ib"):
                response.append("Current data fetched from Interactive Brokers")
            else:
                response.append(self.db.getSource())
        elif(command == "jobs"):
            response.append("")
            response.append("Currently running: " +
                            str(threading.active_count())+" threads.")
        elif(command == ""):
            response.append("")
            response.append("No command sent")
        else:
            response.append("")
            response.append("Unknown command, try help for commands")
        return response

    def consolecommand(self, command=""):
        response = []
        command = command.lower()
        try:
            if (command == "intro" or command == "about"):
                response.append("intro")
            elif(command == "quit" or command == "exit"):
                if input("\n998. Really quit? (y/n)>").lower().startswith('y'):
                    response.append("shutdown")
            elif(command == "help"):
                response.append("")
                response.append(
                    "================================================================")
                response.append(
                    "RobotRay Help Menu - commands and manual override options")
                response.append(
                    "================================================================")
                response.append("")
                response.append(
                    " General Commands: help, clear, status, source, jobs,")
                response.append(
                    "   isdbinuse, quit, exit, intro, about")
                response.append(
                    "----------------------------------------------------------------")
                response.append(
                    " The following are scheduled automatically, run only for override")
                response.append(
                    " Stock Data refresh manual commands: getstockdata, getintradaydata")
                response.append(
                    " Option Data refresh manual commands: getoptiondata")
                response.append(
                    "----------------------------------------------------------------")
                response.append(" Portfolio commands (TBD): switchsource, ")
                response.append("   getPositions, getAccount, getBuyingPower ")
                response.append("   getAvailableFunds, getCash, getUnrPNL, getRPNL ")
                response.append("   getTrades, getOpenTrades, getOpenOrders, getOrders ")
                response.append(
                    "----------------------------------------------------------------")
                response.append(
                    " Stock Data info commands: printstocks, printintra")
                response.append(" Option Data info commands: printoptions")
                response.append(
                    " Run prospect info: printallp, printopenp, printclosedp, sendp")
                response.append(
                    "----------------------------------------------------------------")
                response.append(" Strategies: sellputs, golden")
                response.append(" Backtrader: btdownload, btsellputs, btgolden")
                response.append(
                    "----------------------------------------------------------------")
                response.append(
                    " Statistics for bot operations (TBD): report, reporty, ")
                response.append(
                    "    reportytd, reportsm, reportw")
                response.append(
                    "================================================================")
            elif(command == "clear"):
                response.append("")
                if sys.platform == 'win32':
                    os.system("cls")
                else:
                    os.system("clear")
            elif(command == "isdbinuse"):
                response.append("")
                if(self.db.isDbInUse()):
                    response.append("994. DB is currently: Not used by any thread")
                else:
                    response.append("994. DB is currently: In Use by thread")
            elif (command == "source"):
                response.append("")
                if (self.db.getSource() == "public"):
                    response.append("501. Current data fetched from: Finviz & Yahoo")
                elif (self.db.getSource() == "ib"):
                    response.append("501. Current data fetched from: Interactive Brokers")
                else:
                    response.append("501. "+self.db.getSource())
            # elif (command == "setpassword"):
            #    passwd = getpass.getpass("Enter password:")
            #    keyring.set_password("RobotRayIB", "camilo", passwd)
            #    print(keyring.get_password("RobotRayIB", "camilo"))
            elif (command == "printstocks"):
                response.append("db.printStocks")
                response.append("550. Stocks being tracked:")
            elif (command == "printintra"):
                response.append("db.printIntradayStocks")
                response.append("560. Stocks current intraday data:")
            elif (command == "printoptions"):
                response.append("db.printOptions")
                response.append("570. Options data:")
            elif (command == "printopenp"):
                response.append("sellp.printOpenProspects")
                response.append("130. Open Prospect data:")
            elif (command == "printclosedp"):
                response.append("sellp.printClosedProspects")
                response.append("130. Closed Prospect data:")
            elif (command == "printallp"):
                response.append("sellp.printAllProspects")
                response.append("130. Prospect data:")
            elif(command == "sendp"):
                self.sellp.sendDailyReport()
            elif(command == "status"):
                self.status()
            elif(command == "getstockdata"):
                self.getStockData()
            elif(command == "getintradaydata"):
                self.getIntradayData()
            elif(command == "getoptiondata"):
                self.getOptionData()
            elif(command == "jobs"):
                response.append("")
                response.append("996. Currently running: " +
                                str(threading.active_count())+" threads.")
            elif(command == "golden"):
                self.goldenstrategy()
            elif(command == "sellputs"):
                self.sellputsstrategy()
            elif(command == "btdownload"):
                self.btdownloader()
            elif(command == "dailyscan"):
                self.dailyScan()
            elif(command == "btgolden"):
                self.btgolden()
            elif(command == "btsellputs"):
                self.btsellputs()
            elif(command == ""):
                pass
            else:
                response.append("")
                response.append("Unknown command, try help for commands")
            return response
        except Exception as e:
            self.log.logger.error(e)

    def status(self):
        f = '{:>30}|{:<70}'  # format
        status = self.db.getServerRun()
        for x in range(len(status.columns)):
            self.log.logger.info(f.format(status.columns[x], str(status.iloc[0, x])))

    def ismarketopen(self):
        import datetime
        if (datetime.datetime.today().weekday() < 5) and ((datetime.datetime.now().time() > datetime.time(7, 30)) and
                                                          (datetime.datetime.now().time() < datetime.time(20, 00))):
            return True
        else:
            self.log.logger.info("998. - Market closed or not a working day")
            return False

    def getStockData(self):
        self.log.logger.info("10. Getting stock data, daily process ")
        if self.ismarketopen() or self.oth == "Yes":
            try:
                self.db.getStockData()
                self.log.logger.info(
                    "10. DONE - Stock data fetched")
                self.rrGoldenStrategy.evaluateProspects()
                self.db.updateServerRun(lastStockDataUpdate=datetime.datetime.now())
            except Exception as e:
                self.log.logger.error("10. Error fetching daily stock data")
                self.log.logger.error(e)

    def getOptionData(self):
        self.log.logger.info("20. Getting Option Data")
        if self.ismarketopen() or self.oth == "Yes":
            try:
                self.db.getOptionData()
                self.log.logger.info(
                    "20. DONE - Option data successfully fetched")
                self.db.updateServerRun(lastOptionDataUpdate=datetime.datetime.now())
            except Exception as e:
                self.log.logger.error("20. Error fetching daily option data")
                self.log.logger.error(e)

    def getIntradayData(self):
        self.log.logger.info("30. Getting Intraday Data")
        self.runCycle = self.runCycle + 1
        if self.ismarketopen() or self.oth == "Yes":
            try:
                self.db.getIntradayData()
                self.log.logger.info(
                    "30. DONE - Intraday data successfully fetched")
                self.sellputsstrategy()
            except Exception as e:
                self.log.logger.error("30. Error fetching Intraday data")
                self.log.logger.error(e)

    def dailyScan(self):
        self.log.logger.info("85. Running daily scan")
        if self.ismarketopen() or self.oth == "Yes":
            try:
                self.btdownloader()
                ds = rrDailyScan()
                ds.communicateScan()
                self.log.logger.info(
                    "85. DONE - Ran daily scanner")
            except Exception as e:
                self.log.logger.error("85. Error running daily scann")
                self.log.logger.error(e)

    def btdownloader(self):
        self.log.logger.info("80. Backtrader downloading data")
        if self.ismarketopen() or self.oth == "Yes":
            try:
                self.bt.downloadStockData()
                self.log.logger.info(
                    "80. DONE - Backtrader successfully fetched")
            except Exception as e:
                self.log.logger.error("80. Error fetching backtrader data")
                self.log.logger.error(e)

    def btgolden(self):
        self.log.logger.info("81. Backtrader golden strategy")
        if self.ismarketopen() or self.oth == "Yes":
            try:
                self.bt.btGolden()
                self.log.logger.info(
                    "81. DONE - Backtrader golden strategy")
            except Exception as e:
                self.log.logger.error("81. Error backtrading golden strategy")
                self.log.logger.error(e)

    def btsellputs(self):
        self.log.logger.info("82. Backtrader sell puts strategy")
        if self.ismarketopen() or self.oth == "Yes":
            try:
                self.bt.btGolden()
                self.log.logger.info(
                    "82. DONE - Backtrader sell puts strategy")
            except Exception as e:
                self.log.logger.error("82. Error backtrading sell puts strategy")
                self.log.logger.error(e)

    def goldenstrategy(self):
        self.log.logger.info("200. Initiating Golden Strategy ...")
        if self.ismarketopen() or self.oth == "Yes":
            try:
                self.log.logger.info(
                    "     210. Evaluating changes in SMA50 and SMA200 for intersections of elegible stocks")
                self.rrGoldenStrategy.evaluateProspects()
                self.db.updateServerRun(lastThinkUpdate=datetime.datetime.now())
                self.log.logger.info("200. DONE - Finished strategy")
            except Exception as e:
                self.log.logger.error("200. Error strategy")
                self.log.logger.error(e)

    def sellputsstrategy(self):
        self.log.logger.info(
            "100. Initiating Sell Puts Strategy ...")
        if self.ismarketopen() or self.oth == "Yes":
            try:
                self.log.logger.info(
                    "     110. Evaluating daily drops and pricing opptys for elegible stocks")
                self.sellp.evaluateProspects()
                self.log.logger.info(
                    "     120. Updating pricing for existing prospects")
                self.sellp.updatePricingProspects()
                self.log.logger.info(
                    "     130. Communicating prospects")
                self.sellp.communicateProspects()
                self.log.logger.info(
                    "     140. Communicating closings")
                self.sellp.communicateClosing()
                self.db.updateServerRun(lastThinkUpdate=datetime.datetime.now())
                self.log.logger.info("100. DONE - Finished Sell Puts Strategy")
            except Exception as e:
                self.log.logger.error("100. Error Sell Puts Strategy")
                self.log.logger.error(e)

    def sendReport(self):
        self.log.logger.info(
            "200. Sending report")
        if self.ismarketopen() or self.oth == "Yes":
            try:
                self.sellp.sendDailyReport()
                self.log.logger.info("200. DONE - Finished sending report")
            except Exception as e:
                self.log.logger.error("200. Error sending report")
                self.log.logger.error(e)
