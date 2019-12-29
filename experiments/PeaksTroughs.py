
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime

# The above could be sent to an independent module
import alpaca_backtrader_api
import backtrader as bt
import pandas as pd
import numpy as np
from scipy.signal import find_peaks

ALPACA_PAPER = True
IS_LIVE = False
IS_OPTIMIZE = False
# Optimization history for only long and close
# Stock Start       End         Optimal   Period Return
# GM    2018-01-26 2018-12-18   6
# S&P   2018-01-26 2019-12-18   13        15%
# MSFT  2018-01-26 2019-12-18   19        50%
# MSFT  2018-01-26 2019-12-18   20        35% (without trend checks)
# GM    2018-01-26 2019-12-18   7        -1%
# GM    2018-01-26 2019-12-18   12        20% (Without trend checks)
# DBX   2018-03-26 2019-12-18   6         56% (Without trend checks)


def isPeak(prices):
    dist = len(prices)/2
    ar_prices = np.array(prices)
    ar_peaks, params = find_peaks(ar_prices, distance=dist)
    # print(ar_peaks)
    if (ar_peaks.size > 0) and (ar_peaks[-1] == ar_prices.size-2):
        return True
    else:
        return False


def isTrough(prices):
    dist = len(prices)/2
    ar_prices = np.array(prices)
    ar_troughs, params = find_peaks(-1*ar_prices, distance=dist)
    if (ar_troughs.size > 0) and (ar_troughs[-1] == ar_prices.size-2):
        return True
    else:
        return False


def isPeakTrend(prices):
    # Do not buy if last two troughs are decreasing
    dist = len(prices)/2
    ar_prices = np.array(prices)
    ar_peaks = find_peaks(ar_prices, distance=dist)[0]
    # print(ar_peaks)
    if (ar_peaks.size > 1) and (ar_peaks[-1] == ar_prices.size-2) and (ar_prices[ar_peaks[-1]] >= ar_prices[ar_peaks[-2]]):
        return True
    # elif (ar_peaks.size==1) and (ar_peaks[-1] == ar_prices.size-2):
    #     return True
    else:
        return False


def isTroughTrend(prices):
    dist = len(prices)/2
    ar_prices = np.array(prices)
    ar_troughs = find_peaks(-1*ar_prices, distance=dist)[0]
    # print(prices)
    # print(ar_troughs)
    if (ar_troughs.size > 1) and (ar_troughs[-1] == ar_prices.size-2) and ar_prices[ar_troughs[-1]] >= ar_prices[ar_troughs[-2]]:
        return True
    # elif (ar_troughs.size==1) and (ar_troughs[-1] == ar_prices.size-2):
    #     return True
    else:
        return False

##


class SmaCross(bt.Strategy):

    params = (('period', 20),('stoploss',0.85))

    def __init__(self):
        # print("Init")
        # print(self.p.low)
        self.openStopLoss = []
        self.startcash = cerebro.broker.getcash()
        self.isPeak = bt.ind.ApplyN(func=isPeak, period=self.p.period)
        self.isTrough = bt.ind.ApplyN(func=isTrough, period=self.p.period)

    def notify_cashvalue(init, cash, value):
        #print("Cash:",cash," Pf Value:",value)
        pass

    def notify_trade(init, trade):
        # print("notify_trade",trade.size,trade.dtopen)
        pass

    def notify_order(init, order):
        # print("notify_order",order)
        pass

    def next(self):
        #print("Price{}, Is Peak:{}, Is Trough:{}".format(self.data0[0],self.isPeak[0],self.isTrough[0]))

        if self.isTrough:
            # print("Buy")
            # self.buy()
            ls_orders = self.buy_bracket(stopprice=self.data0*(self.p.stoploss))
            # print(ls_orders)
            self.cancel(ls_orders[2])
            self.openStopLoss.append(ls_orders[1])
        if self.isPeak:
            # print("close")
            for ordr in self.openStopLoss:
                self.cancel(ordr)
            self.openStopLoss = []
            self.close()

    def stop(self):
        pnl = round(self.broker.getvalue() - self.startcash, 2)
        print(' Period:{} Final PnL: {}'.format(
            self.p.period, pnl))

    # def notify_fund(self, cash, value, fundvalue, shares):
    #     print(cash, value, fundvalue, shares)


cerebro = bt.Cerebro()
if IS_OPTIMIZE:
    cerebro = bt.Cerebro(maxcpus=1)
    cerebro.optstrategy(SmaCross, period=np.arange(5, 25))
else:
    cerebro = bt.Cerebro()
    cerebro.addstrategy(SmaCross)

cerebro.addsizer(bt.sizers.PercentSizer, percents=80)
#cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharperatio')

store = alpaca_backtrader_api.AlpacaStore(
    paper=ALPACA_PAPER
)

if IS_LIVE:
    broker = store.getbroker()  # or just alpaca_backtrader_api.AlpacaBroker()
    cerebro.setbroker(broker)
else:
    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(commission=0.0)

DataFactory = store.getdata  # or use alpaca_backtrader_api.AlpacaData

if IS_LIVE:
    data0 = DataFactory(
        dataname='AAPL',
        timeframe=bt.TimeFrame.TFrame("Days"))
else:
    data0 = DataFactory(
        dataname='AIG',
        timeframe=bt.TimeFrame.TFrame("Days"),
        fromdate=pd.Timestamp('2008-01-26'),
        todate=pd.Timestamp('2008-12-18'),
        historical=True)

cerebro.adddata(data0)

print(cerebro.broker.getcash())
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
stats = cerebro.run()
thestat = stats[0]
# print("After cerebro run stats",stats)
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
#print('Analyzer sharperatio:', thestat.analyzers.sharperatio.get_analysis())

if not IS_OPTIMIZE:
    cerebro.plot()
