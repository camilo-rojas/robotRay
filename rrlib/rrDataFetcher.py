# -*- coding: utf-8 -*-

import sys
import os
from bs4 import BeautifulSoup as bs
import urllib
from urllib.error import URLError, HTTPError
import pandas as pd


class StockDataFetcher():
    # StockDataFetcher class

    def __init__(self, symbol):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrLogger import logger
        self.symbol = symbol
        self.log = logger()
        self.log.logger.debug("    Init Stock Data Fetcher "+str(symbol))
        # timeout import
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        self.timeout = int(config['urlfetcher']['Timeout'])

    def getData(self):
        i = 0
        df = pd.DataFrame(columns=['key', 'value'])
        # self.log.logger.info("    About to retreive "+self.symbol)
        try:
            sauce = urllib.request.urlopen(
                "https://finviz.com/quote.ashx?t="+self.symbol, timeout=self.timeout).read()
        except HTTPError as e:
            self.log.logger.error("HTTP Error= "+str(e.code))
            return df
        except URLError as e:
            self.log.logger.error("URL Error= "+str(e.code))
            return df
        else:
            soup = bs(sauce, 'html.parser')

            data = soup.findAll("td", {"class": "snapshot-td2"})

            for tableData in soup.findAll("td", {"class": "snapshot-td2-cp"}):
                df = df.append({'key': tableData.text}, ignore_index=True)
                df.at[i, 'value'] = data[i].text
                i = i+1
            self.log.logger.debug("   Values loaded: \n"+str(df))
            self.log.logger.info(
                "    DONE - Stock Data Fetcher "+str(self.symbol))
            return df

    def getIntradayData(self):
        df = pd.DataFrame(columns=['stock', 'price', '%Change', '%Volume'])
        try:
            sauce = urllib.request.urlopen(
                "https://finance.yahoo.com/quote/"+self.symbol+'?p='+self.symbol, timeout=self.timeout).read()
        except HTTPError as e:
            self.log.logger.error("    HTTP Error= " +
                                  str(e.code)+" for stock "+self.symbol)
            return df
        except URLError as e:
            self.log.logger.error(
                "    URL Error= "+str(e.code)+" for stock "+self.symbol)
            return df
        except Exception as e:
            self.log.logger.error(
                "    General Exception= "+str(e.code)+" for reason "+str(e.reason))
        else:
            try:
                import locale
                locale.setlocale(category=locale.LC_ALL, locale='US')
                soup = bs(sauce, 'html.parser')
                chgpct = soup.find("span", {"data-reactid": "16"}).text
                chgpct = chgpct[chgpct.find("(")+1:chgpct.find(")")]
                av = soup.find("span", {"data-reactid": "49"}).text
                vol = soup.find("span", {"data-reactid": "44"}).text
                av = locale.atoi(av)
                vol = locale.atoi(vol)
                volc = vol/av
                chgpct = float(chgpct.strip('%'))/100
                price = soup.find("span", {"data-reactid": "14"}).text
                df = df.append({'stock': self.symbol, 'price': price,
                                '%Change': chgpct, '%Volume': volc}, ignore_index=True)
                self.log.logger.debug("   Values loaded: \n"+str(df))
                self.log.logger.info(
                    "    DONE - Stock Intraday Data Fetcher "+str(self.symbol))
                return df
            except Exception as e:
                self.log.logger.error(
                    "    General Exception= "+str(e.code)+" for reason "+str(e.reason))
        return df


class OptionDataFetcher():

    def __init__(self, symbol):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrLogger import logger
        self.symbol = symbol
        self.log = logger()
        self.log.logger.debug("    Init Option Data Fetcher for "+symbol)
        # timeout import
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        self.timeout = int(config['urlfetcher']['Timeout'])

    # Strike int, month is int and the number of months after today
    def getData(self, month, strike):
        # https://finance.yahoo.com/quote/WDAY200117P00160000
        # Get the put value for specified month 3-8
        from rrlib.rrOptions import OptionManager
        month = int(month)
        df = pd.DataFrame(columns=['key', 'value'])
        i = 0
        if (3 <= month <= 8):
            try:
                putURL = OptionManager.getPutFormater(
                    self.symbol, month, strike)
                # print(putURL)
                url = "https://finance.yahoo.com/quote/"+putURL
                self.log.logger.debug("    URL \n"+str(url))
                sauce = urllib.request.urlopen(
                    url, timeout=self.timeout).read()
            except HTTPError as e:
                self.log.logger.error(
                    "      HTTP Error= "+str(e.code)+" for stock "+self.symbol)
                return df
            except URLError as e:
                self.log.logger.error(
                    "      URL Error= "+str(e.code)+" for stock "+self.symbol)
                return df
            else:
                soup = bs(sauce, 'html.parser')
                data = soup.findAll(
                    "td", {"class": "Ta(end) Fw(600) Lh(14px)"})
                for tableData in soup.findAll("td", {"class": "C(black) W(51%)"}):
                    df = df.append(
                        {'key': tableData.span.text}, ignore_index=True)
                    try:
                        df.at[i, 'value'] = data[i].span.text
                    except Exception:
                        df.at[i, 'value'] = data[i].text
                    else:
                        df.at[i, 'value'] = data[i].text
                    i = i+1
                if len(df) > 0:
                    price = soup.find(
                        "span", {"class": "Trsdu(0.3s) Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(b)"})
                    self.log.logger.debug(
                        "    Done pricing loaded: \n"+str(price.text))
                    df = df.append(
                        {'key': 'price', 'value': price.text}, ignore_index=True)
                self.log.logger.debug("    Done Option loaded: \n"+str(df))
                self.log.logger.debug(
                    "    Getting Option loaded: "+self.symbol+" for month "+str(month))
                return df
        else:
            self.log.logger.error(
                "    Month outside or range, allowed 3-8 months")
            return df
