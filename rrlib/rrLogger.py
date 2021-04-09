#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 05 2019
robotRay server v1.0
@author: camilorojas

rrLogger class for logging throughout the RobotRay proyect

"""

import logging
import sys
import logging.handlers
import os


class logger:
    def __init__(self):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrColorFormater import ColoredFormatter
        self.logger = logging.getLogger("rrLog")
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler('rrLog.log')
        fh.setLevel(logging.INFO)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        # Create a Formatter for formatting the log messages
        ft = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # Add the Formatter to the Handler
        fh.setFormatter(ft)
        cf = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(cf)
        if (self.logger.hasHandlers()):
            self.logger.handlers.clear()

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
