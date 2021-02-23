#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 15 14:46:12 2018

@author: camilorojas
"""
import urllib
from bs4 import BeautifulSoup as bs
import peewee as pw
import pandas as pd
from rrlib.rrThinker import thinker
from rrlib.rrDataFetcher import StockDataFetcher
from rrlib.rrDataFetcher import OptionDataFetcher
from rrlib.rrOptions import OptionManager
from rrlib.rrDb import rrDbManager
import datetime
import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def print_full(x):
    pd.set_option('display.max_rows', 1000)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 2000)
    pd.set_option('display.float_format', '{:20,.2f}'.format)
    pd.set_option('display.max_colwidth', -1)
    print(x)
    pd.reset_option('display.max_rows')
    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.float_format')
    pd.reset_option('display.max_colwidth')


# print(datetime.datetime.now().time()>datetime.time(17,30))
# print(datetime.time(17,30))
# d0 = datetime.date(2020, 1, 1)
# print(d0-datetime.date.today())
# th = thinker()
# th.evaluateProspects()
# th.sendDailyReport()
# th.communicateProspects()
# th.communicateClosing()
# th.updatePricingProspects()

# History
# odf = OptionDataFetcher("WDAY")
# print(odf.getData(6, 150))
# print(datetime.date.today()+datetime.timedelta(8*365/12))
# sauce=urllib.request.urlopen("https://finance.yahoo.com/quote/CGC?p=CGC").read()
# soup=bs(sauce, "html.parser")
# chgpct=soup.find("span",{"data-reactid":"49"}).text
# print(chgpct)
db = rrDbManager()
# db.initializeDb()
# db.initializeStocks()
# db.getStockData()
# db.initializeExpirationDate()
# db.getIntradayData()
db.getOptionData()
# stock=StockDataFetcher("IZEA")
# print_full(stock.getIntradayData())
# print_full(stock.getPutValue(7))
# db = pw.SqliteDatabase('rrDb.db')
# row={'stock':'SHOP','date':str(datetime.date.today()),'price':'1','prevClose':'1','salesqq':'1%','sales5y':'1%',
#       'beta':'3','roe':'2','roi':'2','recom':'2','earnDate':'2s', 'targetPrice':'-3','shortFloat':'4','shortRatio':'4',
#       'w52High':'5','w52Low':'4','relVolume':'4','sma20':'2','sma50':'4','sma200':'4','perfDay':'5','perfWeek':'2','perfMonth':'4','perfQuarter':'2','perfHalfYear':'4','perfYear':'5','perfYTD':'4'}
# df=pd.DataFrame(columns=['stock','date','price','prevClose','salesqq','sales5y','beta','roe',
#                                'roi','recom','earnDate','targetPrice','shortFloat','shortRatio','w52High',
#                                 'w52Low','relVolume','sma20','sma50','sma200','perfDay','perfWeek','perfMonth',
#                                 'perfQuarter','perfHalfYear','perfYear','perfYTD'])
# df=df.append(row,ignore_index=True)
# StockData.insert(row).execute()
