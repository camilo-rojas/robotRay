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
        self.log.logger.info("10. Getting stock data, daily process ")
        if self.isworkday():
            try:
                self.db.getStockData()
                self.log.logger.info(
                    "10. DONE - Stock data successfully fetched")
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
        schedule.every(4).hours.do(self.run_threaded, self.getStockData)
        schedule.every(5).minutes.do(self.run_threaded, self.getIntradayData)
        schedule.every().day.at("19:50").do(self.run_threaded, self.sendReport)
#        schedule.every(3).minutes.do(self.run_threaded, self.think) moved to intraday fetcher due to conflicts in io

    def runServer(self):
        self.run_threaded(self.runScheduler)
        while True:
            command = input("> ")
            try:
                if (command == "intro" or command == "about"):
                    self.intro()
                elif(command == "quit" or command == "exit"):
                    if input("\nReally quit? (y/n)>").lower().startswith('y'):
                        self.running = False
                        self.shutdown()
                elif(command == "help"):
                    self.log.logger.info("Commands: help, quit, exit, intro, about, jobs")
                elif(command == "jobs"):
                    self.log.logger.info("Currently running: " +
                                         str(threading.active_count())+" threads. Thread info:")
                    for threadStatus in self.threads:
                        self.log.logger.info(str(self.get_thread_info()))
                    self.log.logger.info("End of job information")
                elif(command == ""):
                    pass
                else:
                    self.log.logger.info("Unknown command, try help for commands")
            except KeyboardInterrupt:
                exit_gracefully(signal.SIGINT, exit_gracefully)
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
        if input("\nReally quit? (y/n)>").lower().startswith('y'):
            sys.exit()

    except KeyboardInterrupt:
        print("\nOk, quitting robotRay server")
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
