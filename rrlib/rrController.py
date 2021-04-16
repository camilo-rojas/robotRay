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
import time
import sys
import os
import datetime
import configparser


class rrController():
    def __init__(self, *args, **kwargs):
        # starting common services
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        # starting logging service
        from rrlib.rrLogger import logger
        self.log = logger()
        # starting backend services
        from rrlib.rrDb import rrDbManager
        from rrlib.rrThinker import thinker
        self.db = rrDbManager()
        self.thinker = thinker()
        # starting ini parameters
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        self.log.logger.debug("Initialization finished robotRay controller")

    def command(self, command=""):
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
            response.append(self.thinker.printOpenProspects())
        elif (command == "printclosedp"):
            response.append("Closed Prospect data")
            response.append(self.thinker.printClosedProspects())
        elif (command == "printallp"):
            response.append("All Prospect data sorted by PNL")
            response.append(self.thinker.printAllProspects())
        elif(command == "sendp"):
            response.append("Sent daily report of prospects")
            self.thinker.sendDailyReport()
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
