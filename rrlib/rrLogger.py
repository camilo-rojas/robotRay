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
import tqdm
import io
from copy import copy
from logging import Formatter

MAPPING = {
    'DEBUG': 37,  # white
    'INFO': 36,  # cyan
    'WARNING': 33,  # yellow
    'ERROR': 31,  # red
    'CRITICAL': 41,  # white on red bg
}

PREFIX = '\033['
SUFFIX = '\033[0m'


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)
        # else:
        #    cls._instances[cls].__init__(*args, **kwargs)
        return cls._instances[cls]


class logger(metaclass=Singleton):
    def __init__(self):
        self.logger = logging.getLogger("rrLog")
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler('rrLog.log')
        fh.setLevel(logging.INFO)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        # Create a Formatter for formatting the log messages
        ft = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
        # Add the Formatter to the Handler
        fh.setFormatter(ft)
        cf = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(cf)
        if (self.logger.hasHandlers()):
            self.logger.handlers.clear()

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)


class TqdmToLogger(io.StringIO):
    """
        Output stream for TQDM which will output to logger module instead of
        the StdOut.
    """
    logger = None
    level = None
    buf = ''

    def __init__(self, logger, level=None):
        super(TqdmToLogger, self).__init__()
        self.logger = logger
        self.level = level or logging.INFO

    def write(self, buf):
        self.buf = buf.strip('\r\n\t ')

    def flush(self):
        self.logger.log(self.level, self.buf)


class ColoredFormatter(Formatter):

    def __init__(self, patern):
        Formatter.__init__(self, patern,  datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record):

        colored_record = copy(record)
        levelname = colored_record.levelname

        import platform
        if platform.system() == 'Windows':
            # Windows does not support ANSI escapes and we are using API calls to set the console color
            pass
            # logging.StreamHandler.emit = add_coloring_to_emit_windows(logging.StreamHandler.emit)
        else:
            # all non-Windows platforms are supporting ANSI escapes so we use them
            seq = MAPPING.get(levelname, 37)  # default white
            colored_levelname = ('{0}{1}m{2}{3}').format(
                PREFIX, seq, levelname, SUFFIX)
            colored_record.levelname = colored_levelname
            # comment next line for only status coloring
            colored_record.msg = ('{0}{1}m{2}{3}').format(
                PREFIX, seq, colored_record.getMessage(), SUFFIX)

        return Formatter.format(self, colored_record)  # -*- coding: utf-8 -*-
