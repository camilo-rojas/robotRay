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
import datetime


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
        self.startupTime = datetime.datetime.now()
        self.stockDataUpdateTime = datetime.datetime.now()
        self.optionDataUpdateTime = datetime.datetime.now()
        self.thinkUpdateTime = datetime.datetime.now()
        self.dbFilename = ""

    def intro(self):
        self.log = logger()
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
        # find .ini db filename
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        self.dbFilename = config.get('DB', 'filename')
        # confirm if the file exists
        self.db = rrDbManager()
        if os.path.isfile(self.dbFilename):
            self.log.logger.info(
                "00. RobotRay DB found")
            self.db.initializeDb()
        else:
            # if the file doesn't exist build tables
            self.log.logger.warning(
                "00. RobotRay DB not found")
            self.db.initializeDb()
            self.log.logger.info(
                "00. RobotRay DB created and tables built")
        self.log.logger.info(
            "01. Building db elegible stocks for Option scanning")
        self.db.initializeStocks()
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
        self.log.logger.info(
            "-- Finished Startup robotRay server. Starting schedule.")
        self.log.logger.info("")

    def getStockData(self):
        self.log.logger.info("10. Getting stock data, daily process ")
        if self.isworkday():
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
        if self.isworkday():
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
        if self.isworkday():
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
        if self.isworkday():
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
        if self.isworkday():
            try:
                self.thinker = thinker()
                self.thinker.sendDailyReport()
                self.log.logger.info("200. DONE - Finished sending report")
            except Exception as e:
                self.log.logger.error("200. Error sending report")
                self.log.logger.error(e)

    def testing(self):
        pass
        # self.log.logger.info("99. Testing")

    def scheduler(self):
        schedule.every(4).hours.do(self.run_threaded, self.getStockData)
        schedule.every(10).minutes.do(self.run_threaded, self.getIntradayData)
        schedule.every(22).minutes.do(self.run_threaded, self.getOptionData)
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
        job_thread.daemon = True
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
        try:
            mainserver = server()
            mainserver.startup()
            mainserver.runServer()
        except KeyboardInterrupt:
            exit_gracefully(signal.SIGINT, exit_gracefully)
