#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 05 2019
robotRay server v1.0
@author: camilorojas

Database implementation in SQLLite3

Entities:
    - Stocks to watch
        - Stock KPI's to monitor from Finviz - updated daily
        - Intraday performance - updated every 5 mins overwritten
        - Option Put valuation for operational months - updated every 3 hours -
        tracking months current + 3-8 months
    - Triggers for correct intraday action with monthly recommendation
    - Dates for expiration for Y+5 of option puts

"""

import pandas as pd
import peewee as pw
import datetime
import sys
import os
import time
from tqdm import tqdm

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
db = pw.SqliteDatabase('rrDb.db')


class rrDbManager:

    def __init__(self):
        # Starting common services
        from rrlib.rrLogger import logger, TqdmToLogger
        # Get logging service
        self.log = logger()
        self.tqdm_out = TqdmToLogger(self.log.logger)
        self.log.logger.debug("  DB Manager starting.  ")
        # starting ini parameters
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        # db filename to confirm it exists
        self.dbFilename = config.get('DB', 'filename')
        self.initializeDb()
        # Get list of stocks to track
        self.stocks = config.get('stocks', 'stocks')
        # Get datsource from pubic or ib
        self.source = config.get('datasource', 'source')
        # Get verbose option boolean
        self.verbose = config.get('datasource', 'verbose')

    def initializeDb(self):
        Stock.create_table()
        StockData.create_table()
        ExpirationDate.create_table()
        OptionData.create_table()
        IntradayStockData.create_table()
        ProspectData.create_table()
        ServerRun.create_table()

    def startServerRun(self):
        sr = ServerRun(startup=datetime.datetime.now())
        sr.save()

    def updateServerRun(self, lastStockDataUpdate="", lastOptionDataUpdate="",
                        lastThinkUpdate="", telegramBotEnabled="", runCycles="", prospectsFound="", pnl=""):
        sr = ServerRun.select().order_by(ServerRun.id.desc()).get()
        if telegramBotEnabled != "":
            sr.telegramBotEnabled = "Yes"
        if lastStockDataUpdate != "":
            sr.lastStockDataUpdate = lastStockDataUpdate
        if lastOptionDataUpdate != "":
            sr.lastOptionDataUpdate = lastOptionDataUpdate
        if lastThinkUpdate != "":
            sr.lastThinkUpdate = lastThinkUpdate
            if sr.runCycles == "":
                sr.runCycles = "1"
            else:
                sr.runCycles = str(int(sr.runCycles)+1)
        if prospectsFound != "":
            if sr.prospectsFound == "":
                sr.prospectsFound = "1"
            else:
                sr.prospectsFound = str(int(sr.prospectsFound)+1)
        if pnl != "":
            if sr.pnl == "":
                sr.pnl = pnl
            else:
                sr.pnl = str(float(sr.pnl)+pnl)
        sr.save()

    def getServerRun(self):
        sr = pd.DataFrame(ServerRun.select().order_by(ServerRun.id.desc()).dicts())
        return sr.head(1)

    def isDbInUse(self):
        try:
            status = db.connect()
        except Exception:
            status = False
        return status

    def getSource(self):
        return self.source

    def initializeStocks(self):
        self.log.logger.debug("  DB Manager initializing Stock Table.  ")
        Stock.drop_table(True)
        Stock.create_table()
        stockList = [x.strip() for x in self.stocks.split(',')]
        self.log.logger.debug(stockList)
        stocks = []
        for st in stockList:
            stocks.append({'ticker': st})
        self.log.logger.debug(stocks)
        Stock.insert_many(stocks).execute()

    def getStocks(self):
        df = pd.DataFrame(columns=['ticker'])
        try:
            for stock in Stock.select():
                df = df.append({'ticker': stock.ticker}, ignore_index=True)
        except Exception as e:
            self.log.logger.error(
                "  DB Manager Error. Get Stock Table without table, try initializing.  ")
            self.log.logger.error(e)
        return df

    def getStockData(self):
        from rrlib.rrDataFetcher import StockDataFetcher as stckFetcher
        from rrlib.rrDataFetcher import OptionDataFetcher as optFetcher
        from random import randint
        self.log.logger.debug("  DB Manager Get Stock data.  ")
        StockData.create_table()
        try:
            # for stock in tqdm(Stock.select(), file=self.tqdm_out, desc="  Getting Stock Data:", unit="Stock", ascii=False, ncols=120, leave=False):
            for stock in tqdm(Stock.select(), desc="  Getting Stock Data", unit="Stock", ascii=False, ncols=120, leave=False):
                time.sleep(randint(2, 5))
                self.log.logger.debug(
                    "  DB Manager Attempting to retreive data for "+stock.ticker)
                try:
                    dataFetcher = stckFetcher(stock.ticker).getData()
                    price = float(dataFetcher.iloc[68]['value'])
                    if dataFetcher.iloc[9]['value'] == "-":
                        perfWeek = 0
                    else:
                        perfWeek = float(
                            dataFetcher.iloc[9]['value'].strip('%'))/100
                    if dataFetcher.iloc[15]['value'] == "-":
                        perfMonth = 0
                    else:
                        perfMonth = float(
                            dataFetcher.iloc[15]['value'].strip('%'))/100
                    if dataFetcher.iloc[21]['value'] == "-":
                        perfQuarter = 0
                    else:
                        perfQuarter = float(
                            dataFetcher.iloc[21]['value'].strip('%'))/100
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

                    try:
                        strikes = optFetcher(stock.ticker).getStrikes()
                        if strike not in strikes.values:
                            strike = min(strikes.values, key=lambda x: abs(x-strike))
                    except Exception:
                        self.log.logger.warning("  Exception with strikes for:"+stock.ticker)
                    row = {'stock': stock.ticker, 'strike': str(strike), 'timestamp': str(datetime.datetime.now()),
                           'price': dataFetcher.iloc[68]['value'], 'prevClose': dataFetcher.iloc[62]['value'],
                           'salesqq': dataFetcher.iloc[53]['value'], 'sales5y': dataFetcher.iloc[47]['value'],
                           'beta': dataFetcher.iloc[44]['value'], 'roe': dataFetcher.iloc[36]['value'],
                           'roi': dataFetcher.iloc[42]['value'], 'recom': dataFetcher.iloc[69]['value'],
                           'earnDate': dataFetcher.iloc[65]['value'], 'targetPrice': dataFetcher.iloc[31]['value'],
                           'shortFloat': dataFetcher.iloc[20]['value'], 'shortRatio': dataFetcher.iloc[26]['value'],
                           'w52High': dataFetcher.iloc[43]['value'], 'w52Low': dataFetcher.iloc[49]['value'],
                           'relVolume': dataFetcher.iloc[61]['value'], 'sma20': dataFetcher.iloc[70]['value'],
                           'sma50': dataFetcher.iloc[71]['value'], 'sma200': dataFetcher.iloc[72]['value'],
                           'perfDay': dataFetcher.iloc[74]['value'], 'perfWeek': dataFetcher.iloc[9]['value'],
                           'perfMonth': dataFetcher.iloc[15]['value'], 'perfQuarter': dataFetcher.iloc[21]['value'],
                           'perfHalfYear': dataFetcher.iloc[27]['value'], 'perfYear': dataFetcher.iloc[32]['value'],
                           'perfYTD': dataFetcher.iloc[38]['value']}
                    self.log.logger.debug("  DB Manager Built row:"+str(row))
                    StockData.insert(row).execute()
                    self.log.logger.debug(
                        "  DB Manager DONE Data retreived for "+stock.ticker)
                    if (self.verbose == "Yes"):
                        tqdm.write(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
                                   + " - rrLog - "
                                   + "INFO -     DONE - Data retreived for " +
                                   stock.ticker+", strike: "+str(strike)
                                   + ", price:$" +
                                   str(dataFetcher.iloc[68]['value']) +
                                   ", sales growth QtQ:"+str(dataFetcher.iloc[53]['value'])
                                   + ", earnings date: "+str(dataFetcher.iloc[65]['value'])+", target price:$"+str(dataFetcher.iloc[31]['value']))
                except Exception as e:
                    self.log.logger.error(
                        "  DB Manager Error failed to fetch data for:"+stock.ticker)
                    self.log.logger.error(e)
        except Exception as e:
            self.log.logger.error(
                "  DB Manager Error failed to fetch data.  Please check internet connectivity or finviz.com for availability."
                "  Using cached version.")
            self.log.logger.error(e)
            return False
        # db.close()
        return True

    def getIntradayData(self):
        # try:
        #    db.connect()
        # except Exception:
        #    self.log.logger.warning(" DB already opened ")
        #    return False
        from random import randint
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrDataFetcher import StockDataFetcher as stckFetcher
        IntradayStockData.create_table()
        try:
            for stock in tqdm(Stock.select(), desc="Getting Stock Data:", unit="Stock", ascii=False, ncols=120, leave=False):
                time.sleep(randint(2, 5))
                self.log.logger.debug(
                    "  DB Manager Attempting to retreive intraday data for "+stock.ticker)
                try:
                    dataFetcher = stckFetcher(stock.ticker).getIntradayData()
                    # Calculate kpi
                    pctChange = round(float(dataFetcher.iloc[0]['%Change']), 3)
                    try:
                        higherOptionData = float(OptionData.select(OptionData.kpi).where(
                            (OptionData.stock == stock.ticker) &
                            (OptionData.timestamp > (datetime.datetime.now()-datetime.timedelta(days=4))))
                            .order_by(OptionData.kpi.desc()).get().kpi)
                    except Exception:
                        higherOptionData = 0
                    salesQtQ = float((StockData.select(StockData.salesqq).where(
                        StockData.stock == stock.ticker).order_by(StockData.id.desc()).get().salesqq).strip('%'))/100
                    sma200 = float((StockData.select(StockData.sma200).where(
                        StockData.stock == stock.ticker).order_by(StockData.id.desc()).get().sma200).strip('%'))/100
                    kpi = round(-22*pctChange*0.5+0.1*higherOptionData +
                                salesQtQ*0.3+sma200*0.1+0.1*2*salesQtQ, 3)
                    row = {'stock': stock.ticker, 'price': dataFetcher.iloc[0]['price'], 'pctChange': pctChange,
                           'pctVol': dataFetcher.iloc[0]['%Volume'], 'timestamp': str(datetime.datetime.now()), 'kpi': kpi}
                    # self.log.logger.info("  DB Manager Built row:"+str(row))
                    IntradayStockData.insert(row).on_conflict(conflict_target=[IntradayStockData.stock], update={
                        IntradayStockData.price: dataFetcher.iloc[0]['price'], IntradayStockData.pctChange: pctChange,
                        IntradayStockData.pctVol: dataFetcher.iloc[0]['%Volume'], IntradayStockData.timestamp: str(datetime.datetime.now()),
                        IntradayStockData.kpi: kpi}).execute()
                    if (self.verbose == "Yes"):
                        tqdm.write(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
                                   + " - rrLog - " +
                                   "INFO -     DONE - Stock intraday data retreived for "+stock.ticker +
                                   ", price:$"+str(dataFetcher.iloc[0]['price'])+", % price change:" + str(pctChange) +
                                   "%, % volume change:"+str(dataFetcher.iloc[0]['%Volume']) +
                                   "%, kpi:"+str(kpi))
                    self.log.logger.debug(
                        "  DB Manager intraday data retreived for "+stock.ticker)
                except Exception as e:
                    self.log.logger.warning(
                        "  DB Manager Error failed to fetch intraday data for:"+stock.ticker+". Or several process running at the same time")
                    self.log.logger.warning(e)
        except Exception as e:
            self.log.logger.error(
                "  DB Manager Error failed to fetch intraday data.  Please check internet connectivity "
                "or yahoo.com for availability.  Using cached verssion.")
            self.log.logger.error(e)
            return False
        # db.close()
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
        # db.close()

    def completeExpirationDate(self, monthYear):
        completeDate = ""
        try:
            self.log.logger.debug("    Completing expiration date "+monthYear)
            retreiveDate = ExpirationDate.select().where(
                ExpirationDate.date.contains(monthYear)).get().date
            completeDate = retreiveDate.strftime("%y%m%d")
        except Exception as e:
            self.log.logger.error(
                "    Error completing expiration date "+monthYear)
            self.log.logger.error(e)
            return False
        # db.close()
        return completeDate

    def getOptionData(self):
        # try:
        #    db.connect()
        # except Exception:
        #    self.log.logger.warning(" DB already opened ")
        #    return False
        from rrlib.rrDataFetcher import OptionDataFetcher as optFetcher
        from random import randint
        self.log.logger.info("  DB Manager Get Option data.  ")
        month = 3
        strike = 150
        OptionData.create_table()
        try:
            for stock in tqdm(Stock.select(), desc="Getting Option Data", unit="Stock", ascii=False, ncols=120, leave=False):
                month = 3
                time.sleep(randint(2, 5))
                self.log.logger.debug(stock.ticker)
                mbar = tqdm(total=6, desc="Getting Month Data: ",
                            unit="Month", ascii=False, ncols=120, leave=False)
                if(self.verbose == "Yes"):
                    tqdm.write(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
                               + " - rrLog - INFO -   Retreving option data for "+stock.ticker)
                while month < 9:
                    try:
                        # get strike info from stock data
                        self.log.logger.debug(str(month))
                        strike = int(StockData.select(StockData.strike).where(
                            StockData.stock == stock.ticker).order_by(StockData.id.desc()).get().strike)
                        stockPrice = float(StockData.select(StockData.price).where(
                            StockData.stock == stock.ticker).order_by(StockData.id.desc()).get().price)
                        self.log.logger.debug("  DB Manager Attempting to retreive data for option " +
                                              stock.ticker+" month "+str(month)+" at strike:"+str(strike))
                        dataFetcher = optFetcher(stock.ticker).getData(month, strike)
                        self.log.logger.debug(dataFetcher)
                        if len(dataFetcher.index) > 0:
                            self.log.logger.debug(
                                "  DB Manager Data retreived for option "+stock.ticker+" month "+str(month))
                            # calculate option data pricing and kpi's
                            # rpotential
                            import configparser
                            import calendar
                            config = configparser.ConfigParser()
                            config.read("rrlib/robotRay.ini")
                            R = int(config['thinker']['R'])
                            # calculate number of contracts, use price if its within bid-ask otherwise use midpoint
                            price = float(dataFetcher.iloc[10]['value'])
                            if price < float(dataFetcher.iloc[2]['value']) or price > float(dataFetcher.iloc[3]['value']):
                                price = (float(dataFetcher.iloc[2]['value']) +
                                         float(dataFetcher.iloc[3]['value']))/2
                            if price > 0:
                                contracts = round(2*R/(50*price))
                            else:
                                contracts = 0
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
                            row = {'stock': stock.ticker, 'strike': str(strike), 'price': round(price, 3),
                                   'expireDate': datetime.datetime.strptime(dataFetcher.iloc[5]['value'], '%Y-%m-%d'),
                                   'openPrice': dataFetcher.iloc[1]['value'],
                                   "bid": dataFetcher.iloc[2]['value'], "ask": dataFetcher.iloc[3]['value'],
                                   "dayRange": dataFetcher.iloc[6]['value'], "volume": dataFetcher.iloc[8]['value'],
                                   "openInterest": dataFetcher.iloc[9]['value'], 'timestamp': datetime.datetime.now(),
                                   'contracts': str(contracts), 'stockOwnership': str(round(stockOwnership, 3)),
                                   'withheldBP': str(round(withheldBP, 3)),
                                   'Rpotential': str(round(Rpotential, 3)), 'kpi': str(round(kpi, 3)),
                                   'expectedPremium': str(round(expectedPremium, 3))}
                            self.log.logger.debug(
                                "  DB Manager Built row: strike="+str(strike)+" row:"+str(row))
                            OptionData.insert(row).on_conflict(conflict_target=[OptionData.stock, OptionData.expireDate, OptionData.strike],
                                                               update={OptionData.price: round(price, 3),
                                                                       OptionData.openPrice: dataFetcher.iloc[1]['value'],
                                                                       OptionData.bid: dataFetcher.iloc[2]['value'],
                                                                       OptionData.ask: dataFetcher.iloc[3]['value'],
                                                                       OptionData.dayRange: dataFetcher.iloc[6]['value'],
                                                                       OptionData.volume: dataFetcher.iloc[8]['value'],
                                                                       OptionData.openInterest: dataFetcher.iloc[9]['value'],
                                                                       OptionData.timestamp: datetime.datetime.now(),
                                                                       OptionData.contracts: str(contracts),
                                                                       OptionData.stockOwnership: str(round(stockOwnership, 3)),
                                                                       OptionData.withheldBP: str(round(withheldBP, 3)),
                                                                       OptionData.Rpotential: str(round(Rpotential, 3)),
                                                                       OptionData.kpi: str(round(kpi, 3)),
                                                                       OptionData.expectedPremium: str(round(expectedPremium, 3))}).execute()
                            if (self.verbose == "Yes"):
                                tqdm.write(str(datetime.datetime.now().strftime(
                                    '%Y-%m-%d %H:%M:%S.%f')[:-3])
                                    + " - rrLog - INFO -     DONE - Option data loaded for "+stock.ticker
                                    + ", strike:$"+str(strike)+", for month "+str(month))
                            self.log.logger.debug("    DONE - Option data loaded: " +
                                                  stock.ticker+" for month "+str(month))
                        else:
                            self.log.logger.debug(
                                "    NOT FOUND - No Option for this month")
                            if (self.verbose == "Yes"):
                                tqdm.write(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
                                           + " - rrLog - INFO -     NOT FOUND - No option for "+stock.ticker+", strike:$"+str(strike) +
                                           ", for month "+str(month))

                        month = month+1
                        mbar.update(1)
                    except Exception as e:
                        self.log.logger.warning(
                            "  DB Manager Error failed to fetch data.  Possibly no Stock Data loaded. Or several process running at the same time")
                        self.log.logger.warning(e)
                        month = month+1
                mbar.close()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.log.logger.error(exc_type, fname, exc_tb.tb_lineno)
            self.log.logger.error("  DB Manager error." +
                                  str(e))
            self.log.logger.error(
                "  DB Manager Error failed to fetch data.  Please check internet connectivity or yahoo.com for availability.  Using cached verssion.")
            return False

        # self.log.logger.info("  closing db.  ")
        # db.close()
        return True

    def saveProspect(self, stock, strike, expireDate, price, contracts, stockOwnership,
                     rPotential, kpi, color):
        # try:
        #    db.connect()
        # except Exception:
        #    self.log.logger.error(" DB already opened ")
        #    return False
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
            self.log.logger.error(
                "  DB Manager error saving prospect." + Exception.with_traceback)
        # db.close()
        return True

# Print functions for console or dataframe return from stock, intraday, option list

    def printStocks(self):
        df = pd.DataFrame(list(StockData.select(StockData.stock, StockData.price, StockData.prevClose,
                                                StockData.perfDay, StockData.strike, StockData.salesqq,
                                                StockData.sales5y, StockData.earnDate, StockData.targetPrice,
                                                StockData.perfMonth, StockData.perfQuarter, StockData.perfYTD,
                                                StockData.perfYear).order_by(StockData.timestamp.desc()).dicts()))
        return df.head(len(self.getStocks().index))

    def printIntradayStocks(self):
        df = pd.DataFrame(list(IntradayStockData.select(IntradayStockData.stock, IntradayStockData.price,
                                                        IntradayStockData.pctChange, IntradayStockData.pctVol,
                                                        IntradayStockData.kpi).order_by(IntradayStockData.kpi.desc()).dicts()))
        return df

    def printOptions(self):
        df = pd.DataFrame(list(OptionData.select(OptionData.stock, OptionData.kpi, OptionData.strike, OptionData.price,
                                                 OptionData.expireDate, OptionData.contracts, OptionData.volume,
                                                 OptionData.openInterest).where(
            (OptionData.kpi != "0")
            & (OptionData.timestamp > (datetime.datetime.now()-datetime.timedelta(days=3))))
            .order_by(OptionData.kpi.desc()).dicts()))
        return df


# Data classes from peewee
# Stock entity


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


class ServerRun(pw.Model):
    startup = pw.DateTimeField()
    lastThinkUpdate = pw.DateTimeField(null=True)
    lastStockDataUpdate = pw.DateTimeField(null=True)
    lastOptionDataUpdate = pw.DateTimeField(null=True)
    runCycles = pw.CharField(default="")
    telegramBotEnabled = pw.CharField(null=True)
    prospectsFound = pw.CharField(default="")
    pnl = pw.CharField(default="")

    class Meta:
        database = db
        db_table = "serverRun"
