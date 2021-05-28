#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07 04 2021
robotRay server v1.0
@author: camilorojas

Backtrader for Golden cross and Death cross Strategy


"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader as bt
import math
import datetime


class rrGoldenBt:
    def __init__(self):
        # Starting common services
        from rrlib.rrLogger import logger, TqdmToLogger
        from rrlib.rrBacktrader import rrBacktrader
        from rrlib.rrPortfolio import rrPortfolio
        from rrlib.rrDb import rrDbManager as db
        # Get logging service
        self.log = logger()
        self.tqdm_out = TqdmToLogger(self.log.logger)
        self.log.logger.debug("  Backtrader starting.  ")
        # startup backtrading db
        self.btdb = rrBacktrader()
        self.portfolio = rrPortfolio()
        self.db = db()
        # starting ini parameters
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        # max investment in % terms of porfolio
        self.maxinv = config.get('backtrader', 'maxinv')
        self.timeframe = config.get('backtrader', 'timeframe')
        self.commission = float(config.get('backtrader', 'commission'))
        # Generate Cerebro
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(float(self.portfolio.funds))
        # Get portfoilo total

    def run(self):
        stocks = self.db.getStocks()
        # for index, stock in tqdm(stocks.iterrows(), desc="  Getting Historic Data", unit="Stock", ascii=False, ncols=120, leave=False):
        for index, stock in stocks.iterrows():
            try:
                if stock['ticker'] == "COIN":
                    continue
                # load data feeds
                historicdata = self.btdb.getHistoricData(stock['ticker'])
                feed = bt.feeds.PandasData(dataname=historicdata)
                self.cerebro.adddata(feed, name=stock['ticker'])
            except Exception as e:
                self.log.logger.warning("  BTGolden - Problem loading data.")
                self.log.logger.warning(e)

        # load strategy for backtesting
        self.cerebro.addstrategy(GoldenStrategy, maxinv=self.maxinv)
        # start balance for performance testing
        self.initialbalance = self.cerebro.broker.getvalue()
        # set commision statement
        self.cerebro.broker.setcommission(self.commission)
        # Add a FixedSize sizer according to the stake
        self.cerebro.addsizer(bt.sizers.FixedSize, stake=10)
        # Add analyzers
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpe', riskfreerate=0.1)
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="myDrawDown")
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="myTradeAnalysis")
        self.cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='myar')
        self.cerebro.addanalyzer(bt.analyzers.SQN, _name="mySqn")

        # try to run the cerebro strategies
        try:
            strategies = self.cerebro.run()
            self.strategy = strategies[0]
        except Exception as e:
            self.log.logger.warning("  Cerebro Run exception")
            self.log.logger.warning(e)
        # get final balance for cerebro strategy
        self.finalbalance = self.cerebro.broker.getvalue()
        self.log.logger.info(
            '   Golden Strategy Backtrader')

        # plot the strategy if generates outstanding value
        # TODO: IMPORTANT ! comment the plot.show() function in the cerebro.plot() and include the following code to format width and height
        """     import matplotlib.pyplot as plt
                figs = []
                for stratlist in self.runstrats:
                    for si, strat in enumerate(stratlist):
                        rfig = plotter.plot(strat, figid=si * 100,
                                            numfigs=numfigs, iplot=iplot,
                                            start=start, end=end, use=use)
                        # pfillers=pfillers2)

                        figs.append(rfig)
                        fig = plt.gcf()
                        fig.set_size_inches(width, height)
        """
        figure = self.cerebro.plot(width=32, height=72, dpi=300, tight=False, barupfill=False, bardownfill=False,
                                   style='candle', plotdist=0.5, volume=False, barup='green', valuetags=False, subtxtsize=7, voltrans=0.30)[0][0]
        figure.savefig("rrlib/btreports/golden/" +
                       datetime.datetime.now().strftime("%y-%m-%d")+'.png')
        msg = ("\n\n*** PnL: ***\n"
               "Start capital         : {start_cash:4.2f}\n"
               "Final balance         : {final_balance:4.2f}\n"
               "Total rlzd net profit : {rpl:4.2f}\n"
               "Result winning trades : {result_won_trades:4.2f}\n"
               "Result lost trades    : {result_lost_trades:4.2f}\n"
               "Profit factor         : {profit_factor:4.2f}\n"
               "Total return          : {total_return:4.2f}%\n"
               "Annual return         : {annual_return:4.2f}%\n"
               "Annualized returns    : {ar}\n"
               "Max. money drawdown   : {max_money_drawdown:4.2f}\n"
               "Max. percent drawdown : {max_pct_drawdown:4.2f}%\n\n"
               "*** Trades ***\n"
               "Number of trades      : {total_number_trades:d}\n"
               "    # Open trades     : {open_trades:d}\n"
               "    # Closed trades   : {trades_closed:d}\n"
               "    %winning          : {pct_winning:4.2f}%\n"
               "    %losing           : {pct_losing:4.2f}%\n"
               "    avg money winning : {avg_money_winning:4.2f}\n"
               "    avg money losing  : {avg_money_losing:4.2f}\n"
               "    best winning trade: {best_winning_trade:4.2f}\n"
               "    worst losing trade: {worst_losing_trade:4.2f}\n\n"
               "*** Performance ***\n"
               "Sharpe ratio          : {sharpe_ratio:4.2f}\n"
               "SQN score             : {sqn_score:4.2f}\n"
               "SQN human             : {sqn_human:s}\n\n"
               )
        kpis = self.get_performance_stats()
        # see: https://stackoverflow.com/questions/24170519/
        # python-# typeerror-non-empty-format-string-passed-to-object-format
        kpis = {k: -999 if v is None else v for k, v in kpis.items()}
        self.log.logger.info(msg.format(**kpis))

    def get_performance_stats(self):
        """ Return dict with performace stats for given strategy withing backtest
        """
        st = self.strategy
        dt = st.data._dataname['open'].index
        trade_analysis = st.analyzers.myTradeAnalysis.get_analysis()
        rpl = trade_analysis.pnl.net.total
        total_return = rpl / self.initialbalance
        total_number_trades = trade_analysis.total.total
        trades_closed = trade_analysis.total.closed
        bt_period = dt[-1] - dt[0]
        bt_period_days = bt_period.days
        drawdown = st.analyzers.myDrawDown.get_analysis()
        sharpe_ratio = st.analyzers.mysharpe.get_analysis()['sharperatio']
        sqn_score = st.analyzers.mySqn.get_analysis()['sqn']
        ar = ''
        for key, value in st.analyzers.myar.get_analysis().items():
            ar = ar+str(key)+"="+str(round(value*100, 2))+"%, "
        kpi = {  # PnL
            'start_cash': self.initialbalance,
            'final_balance': self.finalbalance,
            'rpl': rpl,
            'result_won_trades': trade_analysis.won.pnl.total,
            'result_lost_trades': trade_analysis.lost.pnl.total,
            'profit_factor': (-1 * trade_analysis.won.pnl.total / trade_analysis.lost.pnl.total),
            'rpl_per_trade': rpl / trades_closed,
            'total_return': 100 * total_return,
            'annual_return': (100 * (1 + total_return)**(365.25 / bt_period_days) - 100),
            'ar': ar,
            'max_money_drawdown': drawdown['max']['moneydown'],
            'max_pct_drawdown': drawdown['max']['drawdown'],
            # trades
            'total_number_trades': total_number_trades,
            'open_trades': total_number_trades-trades_closed,
            'trades_closed': trades_closed,
            'pct_winning': 100 * trade_analysis.won.total / trades_closed,
            'pct_losing': 100 * trade_analysis.lost.total / trades_closed,
            'avg_money_winning': trade_analysis.won.pnl.average,
            'avg_money_losing':  trade_analysis.lost.pnl.average,
            'best_winning_trade': trade_analysis.won.pnl.max,
            'worst_losing_trade': trade_analysis.lost.pnl.max,
            #  performance
            'sharpe_ratio': sharpe_ratio,
            'sqn_score': sqn_score,
            'sqn_human': self._sqn2rating(sqn_score)
        }
        return kpi

    def _sqn2rating(self, sqn_score):
        """ Converts sqn_score score to human readable rating
        See: http://www.vantharp.com/tharp-concepts/sqn.asp
        """
        if sqn_score < 1.6:
            return "Poor"
        elif sqn_score < 1.9:
            return "Below average"
        elif sqn_score < 2.4:
            return "Average"
        elif sqn_score < 2.9:
            return "Good"
        elif sqn_score < 5.0:
            return "Excellent"
        elif sqn_score < 6.9:
            return "Superb"
        else:
            return "Holy Grail"


class GoldenStrategy(bt.Strategy):
    params = (
        ('exitbars', 5),
        ('smashort', 50),
        ('smalong', 200)
    )

    def __init__(self, maxinv=0.03):
        # start logger service
        from rrlib.rrLogger import logger
        self.log = logger()
        # To keep track of pending orders
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.oneplot = False
        self.maxinv = maxinv

        # Add two MovingAverageSimple indicator and a crossover
        self.inds = dict()
        for i, d in enumerate(self.datas):
            self.inds[d] = dict()
            self.inds[d]['sma1'] = bt.indicators.SimpleMovingAverage(
                d.close, period=self.params.smashort)
            self.inds[d]['sma2'] = bt.indicators.SimpleMovingAverage(
                d.close, period=self.params.smalong)
            self.inds[d]['cross'] = bt.indicators.CrossOver(
                self.inds[d]['sma1'], self.inds[d]['sma2'])

            if i > 0:  # Check we are not on the first loop of data feed:
                if self.oneplot is True:
                    d.plotinfo.plotmaster = self.datas[0]

        # bt.indicators.MACDHisto(self.datas[0])
        # rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)
        # bt.indicators.ATR(self.datas[0], plot=False)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            self.log.logger.debug("Order submited accepted")
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log.logger.debug('BUY EXECUTED, %.2f' % order.executed.price)
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log.logger.debug('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log.logger.debug('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log.logger.debug('OPERATION PROFIT, GROSS '+str(trade.pnl) +
                              ', NET ' + str(trade.pnlcomm))

    def next(self):
        for i, d in enumerate(self.datas):
            dt, dn = self.datetime.date(), d._name
            position = self.getposition(d).size
            self.size = math.floor((float(self.maxinv)*float(self.broker.cash)) /
                                   (d.close*100))
            if not position:  # no market / no orders
                if self.inds[d]['cross'][0] == 1:
                    self.buy(data=d, size=self.size)
                elif self.inds[d]['cross'][0] == -1:
                    self.sell(data=d, size=self.size)
            else:
                if self.inds[d]['cross'][0] == 1:
                    self.close(data=d)
                    self.buy(data=d, size=self.size)
                elif self.inds[d]['cross'][0] == -1:
                    self.close(data=d)
                    self.sell(data=d, size=self.size)
