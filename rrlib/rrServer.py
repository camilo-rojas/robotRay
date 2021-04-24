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
            "01. Building db elegible stocks ")
        self.db = rrDbManager()
        self.db.startServerRun()
        self.db.initializeStocks()
        self.log.logger.info(
            "01. DONE - Building db elegible stocks for strategies")
        self.log.logger.info("02. Setting dates for options")
        self.db.initializeExpirationDate()
        self.log.logger.info(
            "02. DONE - Setting dates for options")
        self.log.logger.info("03. Controller startup sequence")
        self.controller = rrController()
        self.log.logger.info("03. DONE - Controller startup sequence")
        self.log.logger.info("04. Scheduling daily scanners")
        self.stockdatainterval = int(config.get('scheduler', 'stockdatainterval'))
        self.stockintrainterval = int(config.get('scheduler', 'stockintrainterval'))
        self.stockoptioninverval = int(config.get('scheduler', 'stockoptioninverval'))
        self.dailyreport = config.get('scheduler', 'dailyreport')
        self.scheduler()
        self.log.logger.info("04. DONE - Scheduling daily scanners")
        self.startbot = config.get('telegram', 'startbot')
        if (self.startbot == "Yes"):
            self.log.logger.info("05. Starting Telegram bot")
            self.bot = rrTelegram()
            self.db.updateServerRun(telegramBotEnabled="Yes")
            self.log.logger.info("05. DONE - Starting Telegram bot")
        self.log.logger.info(
            "-- Finished Startup robotRay server. Starting schedule.")
        self.log.logger.info("")

    def scheduler(self):
        schedule.every(self.stockdatainterval).hours.do(
            self.run_threaded, self.controller.getStockData)
        schedule.every(self.stockintrainterval).minutes.do(
            self.run_threaded, self.controller.getIntradayData)
        schedule.every(self.stockoptioninverval).minutes.do(
            self.run_threaded, self.controller.getOptionData)
        schedule.every().day.at(self.dailyreport).do(
            self.run_threaded, self.controller.sendReport)

    def runServer(self):
        self.run_threaded(self.runScheduler)
        if (self.startbot == "Yes"):
            self.run_threaded(self.bot.startbot)
        while True:
            try:
                command = input("> ")
                response = self.controller.consolecommand(command)
                if len(response) > 0:
                    for message in response[1:]:
                        self.log.logger.info(message)
                    if response[0] != "":
                        exec(response[0])
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

    def shutdown(self):
        self.log.logger.info("999. - Shutdown initiated")
        self.log.logger.info("999. - Shutdown completed")
        sys.exit()

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
        from rrlib.rrTelegram import rrTelegram
        from rrlib.rrPutSellStrategy import rrPutSellStrategy
        from rrlib.rrController import rrController
        try:
            mainserver = server()
            mainserver.startup()
            mainserver.runServer()
        except KeyboardInterrupt:
            exit_gracefully(signal.SIGINT, exit_gracefully)
