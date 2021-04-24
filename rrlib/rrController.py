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
from rrlib.rrGolgenStrategy import rrGoldenStrategy


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
        self.rrPutSellStrategy = rrPutSellStrategy()
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
            response.append("RobotRay by Camilo Rojas")
        elif(command == "help"):
            response.append(
                "RobotRay help menu - for Telegram")
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
            if (self.db.getSource() == "public"):
                response.append("Current data fetched from: Finviz & Yahoo")
            elif (self.db.getSource() == "ib"):
                response.append("Current data fetched from: Interactive Brokers")
            else:
                response.append(self.db.getSource())
        elif (command == "printstocks"):
            response.append("Stocks being tracked")
            response.append(self.db.printStocks())
        elif (command == "printintra"):
            response.append("Stocks current intraday data")
            response.append(self.db.printIntradayStocks())
        elif (command == "printoptions"):
            response.append("Options data")
            response.append(self.db.printOptions())
        elif (command == "printopenp"):
            response.append("Open Prospect data")
            response.append(self.rrPutSellStrategy.printOpenProspects())
        elif (command == "printclosedp"):
            response.append("Closed Prospect data")
            response.append(self.rrPutSellStrategy.printClosedProspects())
        elif (command == "printallp"):
            response.append("All Prospect data sorted by PNL")
            response.append(self.rrPutSellStrategy.printAllProspects())
        elif(command == "sendp"):
            response.append("Sent daily report of prospects")
            self.rrPutSellStrategy.sendDailyReport()
        elif(command == "status"):
            response.append("Status report RobotRay.")
            if (self.db.getSource() == "public"):
                response.append("Current data fetched from: Finviz & Yahoo")
            elif (self.db.getSource() == "ib"):
                response.append("Current data fetched from Interactive Brokers")
            else:
                response.append(self.db.getSource())
        elif(command == "jobs"):
            response.append("Currently running: " +
                            str(threading.active_count())+" threads.")
        elif(command == ""):
            response.append("No command sent")
        else:
            response.append("Unknown command, try help for commands")
        return response

    def consolecommand(self, command=""):
        response = []
        command = command.lower()
        try:
            if (command == "intro" or command == "about"):
                response.append("self.intro()")
            elif(command == "quit" or command == "exit"):
                if input("\n998. Really quit? (y/n)>").lower().startswith('y'):
                    response.append("self.shutdown()")
            elif(command == "help"):
                response.append("")
                response.append(
                    "================================================================")
                response.append(
                    "RobotRay help menu - commands and manual override options")
                response.append(
                    "================================================================")
                response.append("")
                response.append(
                    "995. General Commands: help, clear, status, source, jobs, isdbinuse, quit, exit, intro, about")
                response.append(
                    "----------------------------------------------------------------")
                response.append(
                    "995. The following are scheduled automatically, run only for override")
                response.append(
                    "995. Stock Data refresh manual commands: getstockdata, getintradaydata")
                response.append(
                    "995. Option Data refresh manual commands: getoptiondata, sellputs")
                response.append(
                    "----------------------------------------------------------------")
                response.append(
                    "995. Stock Data info commands: printstocks, printintra")
                response.append("995. Option Data info commands: printoptions")
                response.append(
                    "995. Run prospect info: printallp, printopenp, printclosedp, sendp")
                response.append(
                    "----------------------------------------------------------------")
                response.append(
                    "995. Statistics for bot operations: report, reporty, reportytd, reportsm, reportw")
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
                response.append("print(self.db.printStocks())")
                response.append("550. Stocks being tracked:")
            elif (command == "printintra"):
                response.append("print(self.db.printIntradayStocks())")
                response.append("560. Stocks current intraday data:")
            elif (command == "printoptions"):
                response.append("print(self.db.printOptions())")
                response.append("570. Options data:")
            elif (command == "printopenp"):
                response.append("print(rrPutSellStrategy().printOpenProspects())")
                response.append("130. Open Prospect data:")
            elif (command == "printclosedp"):
                response.append("print(rrPutSellStrategy().printClosedProspects())")
                response.append("130. Closed Prospect data:")
            elif (command == "printallp"):
                response.append("print(rrPutSellStrategy().printAllProspects())")
                response.append("130. Prospect data:")
            elif(command == "sendp"):
                self.rrPutSellStrategy.sendDailyReport()
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
            elif(command == ""):
                pass
            else:
                response.append("")
                response.append("Unknown command, try help for commands")
            return response
        except Exception as e:
            self.log.logger.error(e)

    def status(self):
        self.log.logger.info(self.db.getServerRun())

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
                self.rrPutSellStrategy.evaluateProspects()
                self.log.logger.info(
                    "     120. Updating pricing for existing prospects")
                self.rrPutSellStrategy.updatePricingProspects()
                self.log.logger.info(
                    "     130. Communicating prospects")
                self.rrPutSellStrategy.communicateProspects()
                self.log.logger.info(
                    "     140. Communicating closings")
                self.rrPutSellStrategy.communicateClosing()
                self.db.updateServerRun(lastThinkUpdate=datetime.datetime.now())
                self.log.logger.info("100. DONE - Finished Sell Puts Strategy")
            except Exception as e:
                self.log.logger.error("100. Error Sell Puts Strategy")
                self.log.logger.error(e)

    def sendReport(self):
        self.log.logger.info(
            "200. Sending report to IFTTT")
        if self.ismarketopen() or self.oth == "Yes":
            try:
                self.rrPutSellStrategy.sendDailyReport()
                self.log.logger.info("200. DONE - Finished sending report")
            except Exception as e:
                self.log.logger.error("200. Error sending report")
                self.log.logger.error(e)
