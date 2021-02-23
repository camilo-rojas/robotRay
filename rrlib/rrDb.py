#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import peewee as pw
import datetime
import sys
import os
import time

"""
Created on 07 05 2019

@author: camilorojas

Database implementation in SQLLite3

Entities:
    - Stocks to watch
        - Stock KPI's to monitor from Finviz - updated daily
        - Intraday performance - updated every 5 mins overwritten
        - Option Put valuation for operational months - updated every 3 hours - tracking months current + 3-8 months
    - Triggers for correct intraday action with monthly recommendation
    - Dates for expiration for Y+5 of option puts

"""

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
db = pw.SqliteDatabase('rrDb.db')


class rrDbManager:

    def __init__(self):
        from rrlib.rrLogger import logger
        self.log = logger()
        self.log.logger.debug("  DB Manager starting.  ")

    def initializeDb(self):
        Stock.create_table()
        StockData.create_table()
        ExpirationDate.create_table()
        OptionData.create_table()
        IntradayStockData.create_table()

    def initializeStocks(self):
        self.log.logger.debug("  DB Manager initializing Stock Table.  ")
        Stock.drop_table(True)
        Stock.create_table()
        stocks = [{'ticker': 'SHOP'}, {'ticker': 'SQ'}, {'ticker': 'NVDA'}, {'ticker': 'BABA'},
                  {'ticker': 'TTD'}, {'ticker': 'NFLX'}, {'ticker': 'HUBS'},
                  {'ticker': 'SPLK'}, {'ticker': 'TEAM'}, {'ticker': 'CRM'},
                  {'ticker': 'WDAY'}, {'ticker': 'PYPL'}, {
                      'ticker': 'VMW'}, {'ticker': 'NTNX'},
                  {'ticker': 'CGC'}]

        Stock.insert_many(stocks).execute()

    def getStocks(self):
        df = pd.DataFrame(columns=['ticker'])
        try:
            for stock in Stock.select():
                df = df.append({'ticker': stock.ticker}, ignore_index=True)
        except Exception:
            self.log.logger.error(
                "  DB Manager Error. Get Stock Table without table, try initializing.  ")
        return df

    def getStockData(self):
        from rrlib.rrDataFetcher import StockDataFetcher as stckFetcher
        from random import randint
        self.log.logger.debug("  DB Manager Get Stock data.  ")
        StockData.create_table()
        try:
            for stock in Stock.select():
                time.sleep(randint(2, 5))
                self.log.logger.debug(
                    "  DB Manager Attempting to retreive data for "+stock.ticker)
                try:
                    dataFetcher = stckFetcher(stock.ticker).getData()
                    price = float(dataFetcher.iloc[65]['value'])
                    perfWeek = float(
                        dataFetcher.iloc[5]['value'].strip('%'))/100
                    perfMonth = float(
                        dataFetcher.iloc[11]['value'].strip('%'))/100
                    perfQuarter = float(
                        dataFetcher.iloc[17]['value'].strip('%'))/100
                    # strikePctg import
                    import configparser
                    config = configparser.ConfigParser()
                    config.read("rrlib/robotRay.ini")
                    strikePctg = float(config['thinker']['strikePctg'])
                    strike = int((price*0.3+price/(1+perfWeek)*0.3+price/(1+perfMonth)
                                  * 0.3+price/(1+perfQuarter)*0.1)*(1-strikePctg))
                    # round
                    if strike < 10:
                        strike = round(strike, 0)
                    elif strike < 1000:
                        strike = round(strike, -1)
                    elif strike > 1000:
                        strike = round(strike, -2)
                    # print(strike)
                    row = {'stock': stock.ticker, 'strike': str(strike), 'timestamp': str(datetime.datetime.now()),
                           'price': dataFetcher.iloc[65]['value'], 'prevClose': dataFetcher.iloc[59]['value'],
                           'salesqq': dataFetcher.iloc[50]['value'], 'sales5y': dataFetcher.iloc[44]['value'],
                           'beta': dataFetcher.iloc[41]['value'], 'roe': dataFetcher.iloc[33]['value'],
                           'roi': dataFetcher.iloc[39]['value'], 'recom': dataFetcher.iloc[66]['value'],
                           'earnDate': dataFetcher.iloc[62]['value'], 'targetPrice': dataFetcher.iloc[28]['value'],
                           'shortFloat': dataFetcher.iloc[16]['value'], 'shortRatio': dataFetcher.iloc[22]['value'],
                           'w52High': dataFetcher.iloc[40]['value'], 'w52Low': dataFetcher.iloc[46]['value'],
                           'relVolume': dataFetcher.iloc[58]['value'], 'sma20': dataFetcher.iloc[67]['value'],
                           'sma50': dataFetcher.iloc[68]['value'], 'sma200': dataFetcher.iloc[69]['value'],
                           'perfDay': dataFetcher.iloc[71]['value'], 'perfWeek': dataFetcher.iloc[5]['value'],
                           'perfMonth': dataFetcher.iloc[11]['value'], 'perfQuarter': dataFetcher.iloc[17]['value'],
                           'perfHalfYear': dataFetcher.iloc[23]['value'], 'perfYear': dataFetcher.iloc[29]['value'],
                           'perfYTD': dataFetcher.iloc[35]['value']}
                    self.log.logger.debug("  DB Manager Built row:"+str(row))
                    StockData.insert(row).execute()
                    self.log.logger.debug(
                        "  DB Manager Data retreived for "+stock.ticker)
                except Exception:
                    self.log.logger.error(
                        "  DB Manager Error failed to fetch data for:"+stock.ticker)
        except Exception:
            self.log.logger.error(
                "  DB Manager Error failed to fetch data.  Please check internet connectivity or finviz.com for availability."
                "  Using cached version.")
            return False
        return True

    def getIntradayData(self):
        from random import randint
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrDataFetcher import StockDataFetcher as stckFetcher
        IntradayStockData.create_table()
        try:
            for stock in Stock.select():
                time.sleep(randint(2, 5))
                self.log.logger.debug(
                    "  DB Manager Attempting to retreive intraday data for "+stock.ticker)
                try:
                    dataFetcher = stckFetcher(stock.ticker).getIntradayData()
                    # Calculate kpi
                    pctChange = float(dataFetcher.iloc[0]['%Change'])
                    try:
                        higherOptionData = float(OptionData.select(OptionData.kpi).where(
                            OptionData.stock == stock.ticker).order_by(OptionData.kpi.desc()).get().kpi)
                    except Exception:
                        higherOptionData = 0
                    salesQtQ = float((StockData.select(StockData.salesqq).where(
                        StockData.stock == stock.ticker).order_by(StockData.id.desc()).get().salesqq).strip('%'))/100
                    sma200 = float((StockData.select(StockData.sma200).where(
                        StockData.stock == stock.ticker).order_by(StockData.id.desc()).get().sma200).strip('%'))/100
                    kpi = -22*pctChange*0.5+0.1*higherOptionData + \
                        salesQtQ*0.3+sma200*0.1+0.1*2*salesQtQ
                    row = {'stock': stock.ticker, 'price': dataFetcher.iloc[0]['price'], 'pctChange': pctChange,
                           'pctVol': dataFetcher.iloc[0]['%Volume'], 'timestamp': str(datetime.datetime.now()), 'kpi': kpi}
                    #  self.log.logger.info("  DB Manager Built row:"+str(row))
                    IntradayStockData.insert(row).on_conflict(conflict_target=[IntradayStockData.stock], update={
                        IntradayStockData.price: dataFetcher.iloc[0]['price'], IntradayStockData.pctChange: pctChange,
                        IntradayStockData.pctVol: dataFetcher.iloc[0]['%Volume'], IntradayStockData.timestamp: str(datetime.datetime.now()),
                        IntradayStockData.kpi: kpi}).execute()
                    self.log.logger.debug(
                        "  DB Manager intraday data retreived for "+stock.ticker)
                except Exception:
                    self.log.logger.error(
                        "  DB Manager Error failed to fetch intraday data for:"+stock.ticker)
        except Exception:
            self.log.logger.error(
                "  DB Manager Error failed to fetch intraday data.  Please check internet connectivity "
                "or yahoo.com for availability.  Using cached verssion.")
            return False
        return True

    def initializeExpirationDate(self):
        def third_friday(which_weekday_in_month, day, month, year):  # third friday sept 2019
            dt = datetime.date(year, month, 1)
            dow_lst = []
            while dt.weekday() != day:
                dt = dt + datetime.timedelta(days=1)
            while dt.month == month:
                dow_lst.append(dt)
                dt = dt + datetime.timedelta(days=7)
            return dow_lst[which_weekday_in_month]

        self.log.logger.debug(
            "  DB Manager initializing Expiration Date Table.  ")
        ExpirationDate.drop_table(True)
        ExpirationDate.create_table()
        month = datetime.datetime.today().month
        year = datetime.datetime.today().year
        self.log.logger.debug(
            "    Populating with 24 months after this month:"+str(month)+" "+str(year))
        x = 1  # iterator
        while x < 24:
            if month == 12:
                year = year+1
                month = 1
            else:
                month = month+1
            ExpirationDate.insert(
                {'date': third_friday(2, 4, month, year)}).execute()
            x = x+1

    def completeExpirationDate(self, monthYear):
        completeDate = ""
        try:
            self.log.logger.debug("    Completing expiration date "+monthYear)
            retreiveDate = ExpirationDate.select().where(
                ExpirationDate.date.contains(monthYear)).get().date
            completeDate = retreiveDate.strftime("%y%m%d")
        except Exception:
            self.log.logger.error(
                "    Error completing expiration date "+monthYear)
            return False
        return completeDate

    def getOptionData(self):
        from rrlib.rrDataFetcher import OptionDataFetcher as optFetcher
        from random import randint
        self.log.logger.debug("  DB Manager Get Option data.  ")
        month = 3
        strike = 150
        OptionData.create_table()
        try:
            for stock in Stock.select():
                month = 3
                time.sleep(randint(2, 5))
                while month < 9:
                    try:
                        # get strike info from stock data
                        strike = int(StockData.select(StockData.strike).where(
                            StockData.stock == stock.ticker).order_by(StockData.id.desc()).get().strike)
                        stockPrice = float(StockData.select(StockData.price).where(
                            StockData.stock == stock.ticker).order_by(StockData.id.desc()).get().price)
                        self.log.logger.debug("  DB Manager Attempting to retreive data for option " +
                                              stock.ticker+" month "+str(month)+" at strike:"+str(strike))
                        dataFetcher = optFetcher(
                            stock.ticker).getData(month, strike)
                        self.log.logger.debug(dataFetcher)
                        if len(dataFetcher.index) > 0:
                            self.log.logger.debug(
                                "  DB Manager Data retreived for option "+stock.ticker+" month "+str(month))
                            # calculate option data pricing and kpi's
                            # rpotential
                            import configparser
                            import calendar
                            import datetime
                            config = configparser.ConfigParser()
                            config.read("rrlib/robotRay.ini")
                            R = int(config['thinker']['R'])
                            # calculate number of contracts, use price if its within bid-ask otherwise use midpoint
                            price = float(dataFetcher.iloc[10]['value'])
                            if price < float(dataFetcher.iloc[2]['value']) or price > float(dataFetcher.iloc[3]['value']):
                                price = (float(dataFetcher.iloc[2]['value']) +
                                         float(dataFetcher.iloc[3]['value']))/2
                            contracts = round(2*R/(50*price))
                            # calculate worst case on stock ownership
                            stockOwnership = contracts*strike*100-price*100
                            # calculate BP withheld to match
                            withheldBP = max(100*contracts*(0.25*stockPrice+price *
                                                            (stockPrice-strike)), 100*contracts*(price+0.1*stockPrice))
                            # calculate R potential from selling
                            Rpotential = 100*contracts*price/R/2
                            # calculate expected premium
                            # minpremium import
                            monthlyPremium = float(
                                config['thinker']['monthlyPremium'])
                            expectedPremium = stockPrice*month*monthlyPremium
                            # kpi checks for month of earnings, number of contracts, r potential, reduce for buying power
                            BP = int(config['thinker']['BP'])
                            EdateMonth = list(calendar.month_abbr).index(StockData.select(StockData.earnDate).where(
                                StockData.stock == stock.ticker).order_by(StockData.id.desc()).get().earnDate[:3])
                            kpi = 0.5 if price > expectedPremium else 0  # pricing premium
                            if contracts < 10:  # contract numbers
                                kpi = kpi+0.1
                            elif 10 < contracts < 20:
                                kpi = kpi+0.05
                            kpi = kpi+Rpotential*0.05  # r potential
                            # reduce kpi based on stock ownership vs buying power
                            kpi = kpi-0.1*(stockOwnership/BP)
                            if EdateMonth % 3 == (datetime.datetime.now().month+month) % 3:
                                kpi = 0
                            row = {'stock': stock.ticker, 'strike': str(strike), 'price': price,
                                   'expireDate': datetime.datetime.strptime(dataFetcher.iloc[5]['value'], '%Y-%m-%d'),
                                   'openPrice': dataFetcher.iloc[1]['value'],
                                   "bid": dataFetcher.iloc[2]['value'], "ask": dataFetcher.iloc[3]['value'],
                                   "dayRange": dataFetcher.iloc[6]['value'], "volume": dataFetcher.iloc[8]['value'],
                                   "openInterest": dataFetcher.iloc[9]['value'], 'timestamp': datetime.datetime.now(),
                                   'contracts': str(contracts), 'stockOwnership': str(stockOwnership), 'withheldBP': str(withheldBP),
                                   'Rpotential': str(Rpotential), 'kpi': str(kpi), 'expectedPremium': str(expectedPremium)}
                            self.log.logger.debug(
                                "  DB Manager Built row: strike="+str(strike)+" row:"+str(row))
                            OptionData.insert(row).on_conflict(conflict_target=[OptionData.stock, OptionData.expireDate, OptionData.strike],
                                                               update={OptionData.price: price, OptionData.openPrice: dataFetcher.iloc[1]['value'],
                                                                       OptionData.bid: dataFetcher.iloc[2]['value'],
                                                                       OptionData.ask: dataFetcher.iloc[3]['value'],
                                                                       OptionData.dayRange: dataFetcher.iloc[6]['value'],
                                                                       OptionData.volume: dataFetcher.iloc[8]['value'],
                                                                       OptionData.openInterest: dataFetcher.iloc[9]['value'],
                                                                       OptionData.timestamp: datetime.datetime.now(),
                                                                       OptionData.contracts: str(contracts), OptionData.stockOwnership: str(stockOwnership),
                                                                       OptionData.withheldBP: str(withheldBP), OptionData.Rpotential: str(Rpotential),
                                                                       OptionData.kpi: str(kpi), OptionData.expectedPremium: str(expectedPremium)}).execute()
                            self.log.logger.info("    DONE - Option data loaded: " +
                                                 stock.ticker+" for month "+str(month))
                        else:
                            self.log.logger.debug(
                                "    No info for Option, not elegible")
                        month = month+1
                    except Exception:
                        self.log.logger.error(
                            "  DB Manager Error failed to fetch data.  Possibly no Stock Data loaded.")
                        month = month+1
        except Exception:
            self.log.logger.error(
                "  DB Manager Error failed to fetch data.  Please check internet connectivity or yahoo.com for availability.  Using cached verssion.")
            return False
        return True

    def saveProspect(self, stock, strike, expireDate, price, contracts, stockOwnership,
                     rPotential, kpi, color):
        try:
            ProspectData.create_table()
            today = datetime.datetime.today()
            row = {
                "stock": stock,
                "dateIdentified": today,
                "strike": strike,
                "expireDate": expireDate,
                "price": price,
                "contracts": contracts,
                "stockOwnership": stockOwnership,
                "Rpotential": rPotential,
                "kpi": kpi,
                "STOcomm": None,
                "BTCcomm": None,
                "currentPrice": price,
                "color": color,
                "pnl": None
            }
            ProspectData.insert(row).on_conflict(conflict_target=[ProspectData.stock, ProspectData.strike, ProspectData.expireDate],
                                                 update={ProspectData.currentPrice: price}).execute()
        except Exception:
            self.log.logger(
                "  DB Manager error saving prospect." + Exception.with_traceback)
        return True

# Stock entity
# Stocks to initiate with: SHOP, SQ, NVDA, BABA, TTD, NFLX, HUBS, SPLK, TEAM, CRM, WDAY, PYPL, VMW, NTNX, CGC, DATA


class Stock(pw.Model):
    ticker = pw.CharField(unique=True)

    class Meta:
        database = db
        db_table = "stock"

# Expiration fridays for options entity


class ExpirationDate(pw.Model):
    date = pw.DateField(unique=True)

    class Meta:
        database = db
        db_table = "expirationDate"

# Stock Data entity
# updated daily


class StockData(pw.Model):
    stock = pw.CharField()
    strike = pw.CharField()
    timestamp = pw.DateTimeField()
    price = pw.CharField()
    prevClose = pw.CharField()
    salesqq = pw.CharField()
    sales5y = pw.CharField()
    beta = pw.CharField()
    roe = pw.CharField()
    roi = pw.CharField()
    recom = pw.CharField()
    earnDate = pw.CharField()
    targetPrice = pw.CharField()
    shortFloat = pw.CharField()
    shortRatio = pw.CharField()
    w52High = pw.CharField()
    w52Low = pw.CharField()
    relVolume = pw.CharField()
    sma20 = pw.CharField()
    sma50 = pw.CharField()
    sma200 = pw.CharField()
    perfDay = pw.CharField()
    perfWeek = pw.CharField()
    perfMonth = pw.CharField()
    perfQuarter = pw.CharField()
    perfHalfYear = pw.CharField()
    perfYear = pw.CharField()
    perfYTD = pw.CharField()

    class Meta:
        database = db
        db_table = "stockData"

# Option Data entity
# updated every 3 hours


class OptionData(pw.Model):
    stock = pw.CharField()
    strike = pw.CharField()
    price = pw.CharField()
    expireDate = pw.DateField()
    openPrice = pw.CharField()
    bid = pw.CharField()
    ask = pw.CharField()
    dayRange = pw.CharField()
    volume = pw.CharField()
    openInterest = pw.CharField()
    timestamp = pw.DateTimeField()
    contracts = pw.CharField()
    stockOwnership = pw.CharField()
    withheldBP = pw.CharField()
    Rpotential = pw.CharField()
    kpi = pw.CharField()
    expectedPremium = pw.CharField()

    class Meta:
        database = db
        db_table = "optionData"
        primary_key = pw.CompositeKey("stock", "expireDate", "strike")

# Intraday Stock Data
# updated 5 mins overwrite


class IntradayStockData(pw.Model):
    stock = pw.CharField(unique=True)
    price = pw.CharField()
    pctChange = pw.CharField()
    pctVol = pw.CharField()
    timestamp = pw.DateTimeField()
    kpi = pw.CharField()

    class Meta:
        database = db
        db_table = "intradayStockData"

# Prospect Oppty data


class ProspectData(pw.Model):
    stock = pw.CharField()
    dateIdentified = pw.DateField()
    strike = pw.CharField()
    expireDate = pw.DateField()
    price = pw.CharField()
    contracts = pw.CharField()
    stockOwnership = pw.CharField()
    Rpotential = pw.CharField()
    kpi = pw.CharField()
    STOcomm = pw.DateField(null=True)
    BTCcomm = pw.DateField(null=True)
    currentPrice = pw.CharField()
    color = pw.CharField()
    pnl = pw.CharField(null=True)

    class Meta:
        database = db
        db_table = "prospectData"
        primary_key = pw.CompositeKey("stock", "strike", "expireDate")
