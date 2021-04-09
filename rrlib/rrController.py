# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on 07 05 2019
robotRay server v1.0
@author: camilorojas

Controller class file that coordinates channel requests and executes with backend commands
"""
import threading
import time
import sys
import os
import datetime


class rrController():
    def __init__(self, *args, **kwargs):
        self.log.logger.debug("Initialization finished robotRay controller")

    def command(self, command=""):
        response = []
        if (command == "intro" or command == "about"):
            self.intro()
        elif(command == "quit" or command == "exit"):
            if input("\n998. Really quit? (y/n)>").lower().startswith('y'):
                self.running = False
                self.shutdown()
        elif(command == "help"):
            self.log.logger.info(
                "================================================================")
            self.log.logger.info(
                "RobotRay help menu - commands and manual override options")
            self.log.logger.info(
                "================================================================")
            self.log.logger.info("")
            self.log.logger.info(
                "995. General Commands: help, clear, status, source, jobs, isdbinuse, quit, exit, intro, about")
            self.log.logger.info(
                "================================================================")
            self.log.logger.info(
                "995. The following are scheduled automatically, run only for override")
            self.log.logger.info(
                "995. Stock Data refresh manual commands: getstockdata, getintradaydata")
            self.log.logger.info(
                "995. Option Data refresh manual commands: getoptiondata, think")
            self.log.logger.info(
                "================================================================")
            self.log.logger.info(
                "995. Stock Data info commands: printstocks, printintra")
            self.log.logger.info("995. Option Data info commands: printoptions")
            self.log.logger.info(
                "995. Run prospect info: printallp, printopenp, printclosedp, sendp")
            self.log.logger.info(
                "================================================================")
            self.log.logger.info(
                "995. Statistics for bot operations: report, reporty, reportytd, reportsm, reportw")
        elif(command == "clear"):
            if sys.platform == 'win32':
                os.system("cls")
            else:
                os.system("clear")
        elif(command == "getoptiondata"):
            self.log.logger.info(
                "20. This will take a couple of minutes, please don't cancel")
            self.getOptionData()
        elif(command == "isdbinuse"):
            if(self.db.isDbInUse()):
                self.log.logger.info("994. DB is currently: Not used by any thread")
            else:
                self.log.logger.info("994. DB is currently: In Use by thread")
        elif (command == "source"):
            if (self.db.getSource() == "public"):
                self.log.logger.info("501. Current data fetched from: Finviz & Yahoo")
            elif (self.db.getSource() == "ib"):
                self.log.logger.info("501. Current data fetched from: Interactive Brokers")
            else:
                self.log.logger.info("501. "+self.db.getSource())
        elif (command == "printstocks"):
            self.log.logger.info("550. Stocks being tracked:")
            print(self.db.printStocks())
        elif (command == "printintra"):
            self.log.logger.info("560. Stocks current intraday data:")
            print(self.db.printIntradayStocks())
        elif (command == "printoptions"):
            self.log.logger.info("570. Options data:")
            print(self.db.printOptions())
        elif (command == "printopenp"):
            self.log.logger.info("130. Open Prospect data:")
            print(thinker().printOpenProspects())
        elif (command == "printclosedp"):
            self.log.logger.info("130. Closed Prospect data:")
            print(thinker().printClosedProspects())
        elif (command == "printallp"):
            self.log.logger.info("130. Prospect data:")
            print(thinker().printAllProspects())
        elif(command == "sendp"):
            self.log.logger.info("140. Sending daily report of prospects")
            thinker().sendDailyReport()
        elif(command == "think"):
            self.log.logger.info("590. Launching thinker")
            self.think()
        elif(command == "status"):
            self.log.logger.info(
                "500. Status report RobotRay. Startup at:"+self.startupTime.strftime("%Y-%m-%d %H:%M:%S"))
            self.log.logger.info(
                "500. Running time: "+str(datetime.datetime.now()-self.startupTime) +
                ". Currently running on "+str(threading.active_count())+" threads.")
            self.log.logger.info(
                "500. Last stock data update: " +
                str(self.stockDataUpdateTime) +
                ", "+str(datetime.datetime.now()
                         - self.stockDataUpdateTime)+" has passed since last run")
            self.log.logger.info("500. Last option data update: " +
                                 str(self.optionDataUpdateTime)+", " +
                                 str(datetime.datetime.now()-self.optionDataUpdateTime) +
                                 " has passed since last run")
            self.log.logger.info("500. Last think process: "+str(self.thinkUpdateTime)
                                 + ", " +
                                 str(datetime.datetime.now() - self.thinkUpdateTime) +
                                 " has passed since last run")
            if (self.db.getSource() == "public"):
                self.log.logger.info("501. Current data fetched from: Finviz & Yahoo")
            elif (self.db.getSource() == "ib"):
                self.log.logger.info("501. Current data fetched from Interactive Brokers")
            else:
                self.log.logger.info("501. "+self.db.getSource())
            self.log.logger.info("500. Run cycle #: "+str(self.runCycle))
        elif(command == "getstockdata"):
            self.log.logger.info(
                "10. This will take a couple of minutes, please don't cancel")
            self.getStockData()
        elif(command == "getintradaydata"):
            self.getIntradayData()
        elif(command == "jobs"):
            self.log.logger.info("996. Currently running: " +
                                 str(threading.active_count())+" threads.")
            # for threadStatus in self.threads:
            #    self.log.logger.info("996 - "+str(threadStatus)
            # self.log.logger.info("996 - End of job information")
        elif(command == ""):
            pass
        else:
            self.log.logger.info("Unknown command, try help for commands")
        return response
