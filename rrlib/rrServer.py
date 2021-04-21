#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 05 2019
robotRay server v1.0
@author: camilorojas

RobotRay main server to coordinate main thread execution and services

"""

import threading
import signal
import schedule
import time
import sys
import os
import datetime
import getpass


class server():
    def __init__(self, *args, **kwargs):
        self.log = logger()
        self.intro()
        # Handle Ctrl - C

        def SigIntHand(SIG, FRM):
            self.log.logger.info(
                "To close wait for prompt and enter quit or exit. Ctrl-C does not exit")

        signal.signal(signal.SIGINT, SigIntHand)
        self.runCycle = 0
        self.threads = []
        self.running = True
        self.startupTime = datetime.datetime.now()
        self.stockDataUpdateTime = datetime.datetime.now()
        self.optionDataUpdateTime = datetime.datetime.now()
        self.thinkUpdateTime = datetime.datetime.now()
        self.dbFilename = ""
        self.log.logger.info("Initialization finished robotRay server")

    def intro(self):
        self.log.logger.info("")
        self.log.logger.info(
            "-----------------------------------------------------------------")
        self.log.logger.info("    ____          __            __   ____               ")
        self.log.logger.info("   / __ \ ____   / /_   ____   / /_ / __ \ ____ _ __  __")
        self.log.logger.info("  / /_/ // __ \ / __ \ / __ \ / __// /_/ // __ `// / / /")
        self.log.logger.info(" / _, _// /_/ // /_/ // /_/ // /_ / _, _// /_/ // /_/ / ")
        self.log.logger.info("/_/ |_| \____//_.___/ \____/ \__//_/ |_| \__,_/ \__, /  ")
        self.log.logger.info("                                               /____/   ")
        self.log.logger.info("robotRay v1.0 - by Camilo Rojas - Jun 8 2019")
        self.log.logger.info(
            "Copyright Camilo Rojas - camilo.rojas@gmail.com")
        self.log.logger.info(
            "-----------------------------------------------------------------  ")
        self.log.logger.info("")

    def startup(self):
        self.log.logger.info("-- Startup robotRay server")
        # starting common services
        # find .ini db filename
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        self.log.logger.info(
            "01. Building db elegible stocks for Option scanning")
        self.db = rrDbManager()
        self.log.logger.info(
            "01. DONE - Building db elegible stocks for Option scanning")
        self.log.logger.info("02. Setting dates and confirming option ")
        self.db.initializeExpirationDate()
        self.log.logger.info(
            "02. DONE - Setting dates and confirming option ")
        self.log.logger.info("03. Stock data startup sequence")
        # self.getStockData()
        self.log.logger.info("03. DONE - Stock data startup sequence")
        self.log.logger.info("04. Scheduling daily scanners")
        self.scheduler()
        self.log.logger.info("04. DONE - Scheduling daily scanners")
        self.startbot = config.get('telegram', 'startbot')
        if (self.startbot == "Yes"):
            self.log.logger.info("05. Starting Telegram bot")
            self.bot = rrTelegram()
            self.log.logger.info("05. DONE - Starting Telegram bot")
        self.log.logger.info(
            "-- Finished Startup robotRay server. Starting schedule.")
        self.log.logger.info("")

    def getStockData(self):
        self.log.logger.info("10. Getting stock data, daily process ")
        if self.ismarketopen():
            # if True:
            try:
                self.db.getStockData()
                self.log.logger.info(
                    "10. DONE - Stock data fetched")
                self.stockDataUpdateTime = datetime.datetime.now()
            except Exception as e:
                self.log.logger.error("10. Error fetching daily stock data")
                self.log.logger.error(e)

    def getOptionData(self):
        self.log.logger.info("20. Getting Option Data")
        if self.ismarketopen():
            # if True:
            try:
                self.db.getOptionData()
                self.log.logger.info(
                    "20. DONE - Option data successfully fetched")
                self.optionDataUpdateTime = datetime.datetime.now()
            except Exception as e:
                self.log.logger.error("20. Error fetching daily option data")
                self.log.logger.error(e)

    def getIntradayData(self):
        self.log.logger.info("30. Getting Intraday Data")
        self.runCycle = self.runCycle + 1
        # if True:
        if self.ismarketopen():
            try:
                self.db.getIntradayData()
                self.log.logger.info(
                    "30. DONE - Intraday data successfully fetched")
                self.stockDataUpdateTime = datetime.datetime.now()
                # run option data fetchers every three iterations
                self.think()
            except Exception as e:
                self.log.logger.error("30. Error fetching Intraday data")
                self.log.logger.error(e)

    def think(self):
        self.log.logger.info(
            "100. Initiating R's catcher...")
        if self.ismarketopen():
            try:
                self.thinker = thinker()
                self.thinkUpdateTime = datetime.datetime.now()
                self.log.logger.info(
                    "     110. Evaluating daily drops and pricing opptys for elegible stocks")
                self.thinker.evaluateProspects()
                self.log.logger.info(
                    "     120. Updating pricing for existing prospects")
                self.thinker.updatePricingProspects()
                self.log.logger.info(
                    "     130. Communicating prospects")
                self.thinker.communicateProspects()
                self.log.logger.info(
                    "     140. Communicating closings")
                self.thinker.communicateClosing()
                self.log.logger.info("100. DONE - Finished thinking")
            except Exception as e:
                self.log.logger.error("100. Error thinking")
                self.log.logger.error(e)

    def sendReport(self):
        self.log.logger.info(
            "200. Sending report to IFTTT")
        if self.ismarketopen():
            try:
                self.thinker = thinker()
                self.thinker.sendDailyReport()
                self.log.logger.info("200. DONE - Finished sending report")
            except Exception as e:
                self.log.logger.error("200. Error sending report")
                self.log.logger.error(e)

    def scheduler(self):
        schedule.every(4).hours.do(self.run_threaded, self.getStockData)
        schedule.every(20).minutes.do(self.run_threaded, self.getIntradayData)
        schedule.every(35).minutes.do(self.run_threaded, self.getOptionData)
        schedule.every().day.at("19:50").do(self.run_threaded, self.sendReport)

    def runServer(self):
        self.run_threaded(self.runScheduler)
        if (self.startbot == "Yes"):
            self.run_threaded(self.bot.startbot)
        while True:
            try:
                command = input("> ")
                response = rrController().consolecommand(command)
                if len(response) > 0:
                    for message in response[1:]:
                        self.log.logger.info(message)
                    if response[0] != "":
                        exec(response[0])
            except KeyboardInterrupt:
                self.running = False
                self.shutdown()
                break

    def status(self):
        print("Status is ok")

    def runScheduler(self):
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def run_threaded(self, job_func):
        job_thread = threading.Thread(target=job_func)
        job_thread.daemon = True
        job_thread.start()
        self.threads.append(job_thread)

    def shutdown(self):
        self.log.logger.info("999. - Shutdown initiated")
        # for threadtokill in self.threads:
        #    threadtokill.join()
        self.log.logger.info("999. - Shutdown completed")
        sys.exit()

    def ismarketopen(self):
        import datetime
        if (datetime.datetime.today().weekday() < 5) and ((datetime.datetime.now().time() > datetime.time(7, 30)) and
                                                          (datetime.datetime.now().time() < datetime.time(20, 00))):
            return True
        else:
            self.log.logger.info("998. - Market closed or not a working day")
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
        from rrlib.rrTelegram import rrTelegram
        from rrlib.rrController import rrController
        import keyring
        try:
            mainserver = server()
            mainserver.startup()
            mainserver.runServer()
        except KeyboardInterrupt:
            exit_gracefully(signal.SIGINT, exit_gracefully)
