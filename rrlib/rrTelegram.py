#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 04 2021
robotRay server v1.0
@author: camilorojas

Telegram chat implementation for RobotRay for two way communication on operational status

"""

import datetime
import sys
import os
import time
import configparser
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Dispatcher


class rrTelegram:
    def __init__(self, *args, **kwargs):
        # starting common services
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        # starting logging
        from rrlib.rrLogger import logger
        self.log = logger()
        # starting backend services
        from rrlib.rrDb import rrDbManager
        from rrlib.rrPutSellStrategy import rrPutSellStrategy as rps
        from rrlib.rrController import rrController
        self.db = rrDbManager()
        self.sellp = rps()
        self.cont = rrController()
        # starting ini parameters
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        # Telegram API key & chat id for secure comms
        self.APIkey = config.get('telegram', 'api')
        self.chatid = config.get('telegram', 'chatid')
        self.startBot = config.get('telegram', 'startbot')
        self.log.logger.debug("  rrTelegram module starting.  ")
        # starting bot
        # self.bot = telegram.bot(self.APIkey)
        self.upd = Updater(self.APIkey)
        self.dp = self.upd.dispatcher

    # function to handle the /start command
    def start(self, update, context):
        first_name = update.message.chat.first_name
        self.chat_id = update.message.chat_id
        if(str(self.chat_id) == str(self.chatid)):
            update.message.reply_text(
                f"Hi {first_name}, RobotRay ready for you.")
        else:
            update.message.reply_text("Hi you are not authorized")

    # function to handle the /help command
    def help(self, update, context):
        if(str(self.chat_id) == str(self.chatid)):
            update.message.reply_text('RobotRay help menu, following the options available:')
        else:
            update.message.reply_text("Hi you not authorized")

    # function to handle errors occured in the dispatcher
    def error(self, update, context):
        try:
            update.message.reply_text('RobotRay error occured.')
        except Exception:
            self.log.logger.error(
                "   Robotray error ocurred, you have two instances running Telegram bot")

    # function to handle normal text
    def textCommand(self, update, context):
        text_received = update.message.text
        response = self.cont.botcommand(text_received)
        if len(response) > 0:
            for message in response[1:]:
                update.message.reply_text(f'{message}')
            if response[0] != "":
                if response[0].startswith("db."):
                    func = getattr(self.db, response[0].split("db.", 1)[1])
                    if response[0].split("db.", 1)[1].startswith("print"):
                        print(func())
                    else:
                        func()
                elif response[0].startswith("sellp."):
                    func = getattr(self.sellp, response[0].split("sellp.", 1)[1])
                    if response[0].split("sellp.", 1)[1].startswith("print"):
                        print(func())
                    else:
                        func()
                else:
                    func = getattr(self, response[0])
                    func()

    def startbot(self):
        self.dp.add_handler(CommandHandler("start", self.start))
        self.dp.add_handler(CommandHandler("help", self.help))
        self.dp.add_handler(MessageHandler(Filters.text, self.textCommand))
        self.dp.add_error_handler(self.error)
        # start the bot
        self.upd.start_polling()

    def sendMessage(self, message=""):
        if self.startBot != "No":
            self.upd.bot.send_message(self.chatid, text=message)
