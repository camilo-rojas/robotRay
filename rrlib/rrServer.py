#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 05 2019
robotRay server v1.0
@author: camilorojas
"""

# Main Server code
# Dependencies: anjos.schedule, conda-forge.peewee, requests
# Scrapping info using BS4 with finance.yahoo.com and finviz.com
import threading
import signal
import schedule
import time
import sys
import os


# To do's
# 1. Set parameters for Db initialization at startup
# 3. Progression counters for data downloads and jobs
# 4. Integration with IFTT to alert home assistant or myself on new oportunities


class server():
    def __init__(self, *args, **kwargs):
        self.intro()
        # add logic for argument based initalization and parametization.
        # runCycle takes care of amount of intraday fetches

        def SigIntHand(SIG, FRM):
            self.log.logger.info(
                "To close wait for prompt and enter quit or exit. Ctrl-C does not exit")

        signal.signal(signal.SIGINT, SigIntHand)
        self.runCycle = 0
        self.threads = []
        self.running = True
        self.log.logger.info("Initialization finished robotRay server")

    def intro(self):
        self.log = logger()
        self.log.logger.info("")
        self.log.logger.info(
            "-----------------------------------------------")
        self.log.logger.info("robotRay v1.0 - by Camilo Rojas - Jun 8 2019")
        self.log.logger.info(
            "Copyright Camilo Rojas - camilo.rojas@gmail.com")
        self.log.logger.info(
            "-----------------------------------------------")
        self.log.logger.info("")

    def startup(self):
        self.log.logger.info("-- Startup robotRay server")
        self.log.logger.info(
            "00. Confirming sqllite db buildup and integrity")
        # add logic to read .ini file and save it somewhere
        self.log.logger.info(
            "00. DONE - Confirming sqllite db buildup and integrity")
        self.log.logger.info(
            "01. Building db elegible stocks for Option scanning")
        self.db = rrDbManager()
        self.db.initializeStocks()
        self.log.logger.info(
            "01. DONE - Building db elegible stocks for Option scanning")
        self.log.logger.info("02. Setting dates and confirming option ")
        self.db.initializeExpirationDate()
        self.log.logger.info(
            "02. DONE - Setting dates and confirming option ")
        self.log.logger.info("03. Stock data startup sequence")
        self.getStockData()
        self.log.logger.info("03. DONE - Stock data startup sequence")
        self.log.logger.info("04. Scheduling daily scanners")
        self.scheduler()
        self.log.logger.info("04. DONE - Scheduling daily scanners")
        self.log.logger.info(
            "-- Finished Startup robotRay server. Starting schedule.")
        self.log.logger.info("")

    def getStockData(self):
        self.log.logger.info("10. Getting stock data, hourly process ")
        if self.isworkday():
            try:
                self.db.getStockData()
                self.log.logger.info(
                    "10. DONE - Stock data fetched")
            except Exception:
                self.log.logger.error("10. Error fetching daily stock data")

    def getOptionData(self):
        self.log.logger.info("20. Getting Option Data")
        if self.isworkday():
            try:
                self.db.getOptionData()
                self.log.logger.info(
                    "20. DONE - Option data successfully fetched")
            except Exception:
                self.log.logger.error("20. Error fetching daily option data")

    def getIntradayData(self):
        self.log.logger.info("30. Getting Intraday Data")
        self.runCycle = self.runCycle + 1
        if self.isworkday():
            try:
                self.db.getIntradayData()
                self.log.logger.info(
                    "30. DONE - Intraday data successfully fetched")
                # run option data fetchers every three iterations
                if self.runCycle % 3 == 0:
                    self.getOptionData()
                self.think()
            except Exception:
                self.log.logger.error("30. Error fetching Intraday data")

    def think(self):
        self.log.logger.info(
            "100. Initiating R's catcher...")
        if self.isworkday():
            try:
                self.thinker = thinker()
                self.log.logger.info(
                    "     110. Evaluating daily drops and pricing opptys for elegible stocks")
                self.thinker.evaluateProspects()
                self.log.logger.info(
                    "     120. Updating pricing for existing prospects")
                self.thinker.updatePricingProspects()
                self.log.logger.info(
                    "     130. Communicating prospects to Camilor")
                self.thinker.communicateProspects()
                self.log.logger.info(
                    "     140. Communicating closings to Camilor")
                self.thinker.communicateClosing()
                self.log.logger.info("100. DONE - Finished thinking")
            except Exception:
                self.log.logger.error("100. Error thinking")

    def sendReport(self):
        self.log.logger.info(
            "200. Sending report to Camilor")
        if self.isworkday():
            try:
                self.thinker = thinker()
                self.thinker.sendDailyReport()
                self.log.logger.info("200. DONE - Finished sending report")
            except Exception:
                self.log.logger.error("200. Error sending report")

    def testing(self):
        pass
        # self.log.logger.info("99. Testing")

    def scheduler(self):
        schedule.every(1).hours.do(self.run_threaded, self.getStockData)
        schedule.every(5).minutes.do(self.run_threaded, self.getIntradayData)
        schedule.every().day.at("19:50").do(self.run_threaded, self.sendReport)
#        schedule.every(3).minutes.do(self.run_threaded, self.think) moved to intraday fetcher due to conflicts in io

    def runServer(self):
        self.run_threaded(self.runScheduler)
        while True:
            try:
                command = input("> ")
                if (command == "intro" or command == "about"):
                    self.intro()
                elif(command == "quit" or command == "exit"):
                    if input("\n998 - Really quit? (y/n)>").lower().startswith('y'):
                        self.running = False
                        self.shutdown()
                elif(command == "help"):
                    self.log.logger.info(
                        "995 - General Commands: help, clear, jobs, isdbinuse, quit, exit, intro, about")
                    self.log.logger.info(
                        "995 - The following are scheduled automatically, run only for override")
                    self.log.logger.info(
                        "995 - Stock Data manual commands: getstockdata, getintradaydata, think")
                    self.log.logger.info(
                        "995 - Option Data manual commands: getoptiondata")
                    self.log.logger.info(
                        "995 - Run prospect info: getprospects, sendprospects")
                elif(command == "clear"):
                    if sys.platform == 'win32':
                        os.system("cls")
                    else:
                        os.system("clear")
                elif(command == "getoptiondata"):
                    self.log.logger.info(
                        "20 - This will take a couple of minutes, please don't cancel")
                    self.getOptionData()
                elif(command == "isdbinuse"):
                    if(self.db.isDbInUse()):
                        self.log.logger.info("994 - DB is currently: Not used by any thread")
                    else:
                        self.log.logger.info("994 - DB is currently: In Use by thread")
                elif(command == "getprospects"):
                    self.log.logger.info("130 - Getting prospects (soon)")
                elif(command == "sendprospects"):
                    self.log.logger.info("140 - Sending prospects (soon)")
                elif(command == "status"):
                    self.log.logger.info(
                        "500 - Status report RobotRay. Running for X minutes. Currently running on "+str(threading.active_count())+" threads.")
                    self.log.logger.info(
                        "500 - Last stock data update: XXX, Last option data update: XXX")
                    self.log.logger.info("500 - Currently getting data from: Finviz + Yahoo")
                    self.log.logger.info("500 - Last think process: XXX")
                elif(command == "getstockdata"):
                    self.log.logger.info(
                        "10 - This will take a couple of minutes, please don't cancel")
                    self.getStockData()
                elif(command == "getintradaydata"):
                    self.getIntradayData()
                elif(command == "jobs"):
                    self.log.logger.info("996 - Currently running: " +
                                         str(threading.active_count())+" threads.")
                    # for threadStatus in self.threads:
                    #    self.log.logger.info("996 - "+str(self.get_thread_info()))
                    # self.log.logger.info("996 - End of job information")
                elif(command == ""):
                    pass
                else:
                    self.log.logger.info("Unknown command, try help for commands")
            except KeyboardInterrupt:
                self.running = False
                self.shutdown()
                break

    def runScheduler(self):
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def run_threaded(self, job_func):
        job_thread = threading.Thread(target=job_func)
        job_thread.start()
        self.threads.append(job_thread)

    def get_thread_info(myThread):
        return str(myThread)

    def shutdown(self):
        self.log.logger.info("999. - Shutdown initiated")
        for threadtokill in self.threads:
            threadtokill.join()
        self.log.logger.info("999. - Shutdown completed")
        sys.exit()

    def isworkday(self):
        import datetime
        if (datetime.datetime.today().weekday() < 5) and ((datetime.datetime.now().time() > datetime.time(7, 30)) and
                                                          (datetime.datetime.now().time() < datetime.time(20, 00))):
            return True
        else:
            return False

# Exit signal management from server handler


def exit_gracefully(signum, frame):
    signal.signal(signal.SIGINT, original_sigint)
    try:
        if input("\n998. - Really quit? (y/n)>").lower().startswith('y'):
            sys.exit()

    except KeyboardInterrupt:
        print("\n998. - Ok, quitting robotRay server")
        sys.exit()


# main server run procedure
if __name__ == '__main__':
    while True:
        original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, exit_gracefully)
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrLogger import logger
        from rrlib.rrDb import rrDbManager
        from rrlib.rrThinker import thinker
        try:
            mainserver = server()
            mainserver.startup()
            mainserver.runServer()
        except KeyboardInterrupt:
            exit_gracefully(signal.SIGINT, exit_gracefully)
