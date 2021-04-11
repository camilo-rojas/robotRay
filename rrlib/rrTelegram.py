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
        from rrlib.rrController import rrController
        self.db = rrDbManager()
        self.cont = rrController()
        # starting ini parameters
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        # Telegram API key & chat id for secure comms
        self.APIkey = config.get('telegram', 'api')
        self.chatid = config.get('telegram', 'chatid')
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
        update.message.reply_text('RobotRay error occured.')

    # function to handle normal text
    def textCommand(self, update, context):
        text_received = update.message.text
        response = self.cont.command(text_received)
        for x in response:
            update.message.reply_text(f'{x}')

    def startbot(self):
        self.dp.add_handler(CommandHandler("start", self.start))
        self.dp.add_handler(CommandHandler("help", self.help))
        self.dp.add_handler(MessageHandler(Filters.text, self.textCommand))
        self.dp.add_error_handler(self.error)
        # start the bot
        self.upd.start_polling()

    def sendMessage(self, message=""):
        self.upd.bot.send_message(self.chatid, text=message)
