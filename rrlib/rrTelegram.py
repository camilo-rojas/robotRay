#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import sys
import os
import time
import configparser
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Dispatcher


"""
Created on 07 05 2019

@author: camilorojas

Telegram chat implementation for RobotRay for two way communication on operational status

"""


class rrTelegram:
    def __init__(self, *args, **kwargs):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrLogger import logger
        from rrlib.rrDb import rrDbManager
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        self.log = logger()
        self.log.logger.debug("  Thinker module starting.  ")
        self.db = rrDbManager()
        # Telegram API key
        self.APIkey = config.get('telegram', 'api')
        # starting bot
        # self.bot = telegram.bot(self.APIkey)
        self.upd = Updater(self.APIkey)
        self.dp = self.upd.dispatcher

    # function to handle the /start command
    def start(self, update, context):
        first_name = update.message.chat.first_name
        update.message.reply_text(f"Hi {first_name}, RobotRay ready for you")

    # function to handle the /help command
    def help(self, update, context):
        update.message.reply_text('help command received')

    # function to handle errors occured in the dispatcher
    def error(self, update, context):
        update.message.reply_text('an error occured')

    # function to handle normal text
    def textCommand(self, update, context):
        text_received = update.message.text
        update.message.reply_text(f'did you said "{text_received}" ?')

    def startbot(self):
        self.dp.add_handler(CommandHandler("start", self.start))
        self.dp.add_handler(CommandHandler("help", self.help))
        self.dp.add_handler(MessageHandler(Filters.text, self.textCommand))
        self.dp.add_error_handler(self.error)
        # start the bot
        self.upd.start_polling()
