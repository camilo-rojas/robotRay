#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 15 14:46:12 2018
robotRay server v1.0
@author: camilorojas

Optin Manager class for put formating and supporting tools
"""
import datetime
import sys
import os


class OptionManager:

    def getPutFormater(stock, expiration, strike):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        month = int(expiration)
        month = datetime.date.today()+datetime.timedelta(month*365/12)
        ym = month.strftime("%y-%m")
        from rrlib.rrDb import rrDbManager
        db = rrDbManager()
        ymd = db.completeExpirationDate(ym)
        if strike < 10:
            trailer = "P0000"
        elif strike < 100:
            trailer = "P000"
        elif strike < 1000:
            trailer = "P00"
        elif strike < 10000:
            trailer = "P0"
        else:
            trailer = "P"
        return str(stock+ymd+trailer+str(strike)+"000")

    def getDatebyMonth(month):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrDb import rrDbManager
        db = rrDbManager()
        return db.getDatebyMonth(month)
