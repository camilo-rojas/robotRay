#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 05 2019
robotRay server v1.0
@author: camilorojas

Color formater for the log file and console

"""

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


class ColoredFormatter(Formatter):

    def __init__(self, patern):
        Formatter.__init__(self, patern)

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
