#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 04 2021
robotRay server v1.0
@author: camilorojas

Portfolio classes

Process for module
1. if source is ib then get portfolio total from ib
2. if source is public then get portfolio total from .ini file
3. class lifecycle methods

"""


class rrPortfolio:
    def __init__(self):
        # Starting common services
        from rrlib.rrLogger import logger, TqdmToLogger
        from rrlib.rrDb import rrDbManager
        # Get logging service
        self.db = rrDbManager()
        self.log = logger()
        self.tqdm_out = TqdmToLogger(self.log.logger)
        self.log.logger.debug("  Backtrader starting.  ")
        # starting ini parameters
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        # db filename to confirm it exists
        self.dbFilename = config.get('backtrader', 'filename')
        self.timeframe = config.get('backtrader', 'timeframe')
        self.initializeDb()
        # Get datsource from pubic or ib
        self.source = config.get('datasource', 'source')
        # Get verbose option boolean
        self.verbose = config.get('datasource', 'verbose')
