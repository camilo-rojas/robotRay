#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 04 2021
robotRay server v1.0
@author: camilorojas

IFTT message implementation for RobotRay for one way communication on operational status

"""

import datetime
import sys
import os
import time
import configparser
import requests


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)
        # else:
        #    cls._instances[cls].__init__(*args, **kwargs)
        return cls._instances[cls]


class rrIFTTT(metaclass=Singleton):

    def __init__(self, *args, **kwargs):
        # starting common services
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        # starting logging
        from rrlib.rrLogger import logger
        self.log = logger()
        # starting ini parameters
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        # Telegram API key & chat id for secure comms
        self.IFTTT = config['ifttt']['key']
        self.url = config['ifttt']['url']
        self.log.logger.debug("  rrIFTTT module starting.  ")

    def send(self, report):
        if self.IFTTT != "":
            try:
                r = requests.post(
                    self.url+self.IFTTT, data=report)
                if r.status_code == 200:
                    self.log.logger.debug("    sent message")
                return r
            except Exception as e:
                self.log.logger.error("     IFTTT error:")
                self.log.logger.error(e)
