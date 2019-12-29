
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime

# The above could be sent to an independent module
import alpaca_backtrader_api
import backtrader as bt
import pandas as pd
import numpy as np

ALPACA_PAPER = True
IS_LIVE = False
IS_OPTIMIZE = False
DEBUG = False


class DStrategy(bt.Strategy):

    params = (('low', -0.007), ('high', 0.011), ('period', 3))

    def __init__(self):
        self.time_fl = ""
        if not IS_OPTIMIZE:
            print("Initializing strategy")
        self.startcash = cerebro.broker.getcash()
        #self.add_timer(bt.timer.SESSION_START)
        self.ret0 = bt.ind.PctChange(self.data0.open, period=self.p.period)
        self.ret1 = bt.ind.PctChange(self.data1.open, period=self.p.period)
   
    def prenext(self):
        if DEBUG:
            print("prenext")

    def next(self):
        if DEBUG:
            print("next", self.ret0[0])

        cash = self.broker.getcash()
        position0=self.broker.getposition(data0)
        position1=self.broker.getposition(data1)
    
        if DEBUG:
            print("Stock prices", self.data0, self.data1)
        if(self.ret0[0] < self.p.low):
            if cash > data0:
                self.buy(data0)
        elif (self.ret0[0] > self.p.high):
            if position0.size>0:
                self.sell(data0)

        if(self.ret1[0] < self.p.low):
            if cash > data1:
                self.buy(data1)
        elif (self.ret1[0] > self.p.high):
            if position1.size>0:
                self.sell(data1)

    def notify_store(self,msg):
        if DEBUG:
            print("notify_store",msg)
    
    def notify_data(self,data,status):
        if DEBUG:
            for x in data:
                print(x)
            print("notify_data",data,status)

    def notify_timer(self, timer, when):
        if DEBUG:
            print("notify_timer", self.ret0, self.ret1)
        if len(self.ret0) ==0:
            return
        # Alpaca API in live sends events for past dates we dont want to process those
        if IS_LIVE & (when.date() != datetime.datetime.today().date()):
            return
        print("line44",when,self.time_fl)
        print(when == self.time_fl)
        if when == self.time_fl:
            return
        self.time_fl=when

        cash = self.broker.getcash()
        position0=self.broker.getposition(data0)
        position1=self.broker.getposition(data1)
    
        if DEBUG:
            print("notify_timer called on", when)
            print("Stock prices", self.data0, self.data1)
        if(self.ret0[0] < self.p.low):
            if cash > data0:
                self.buy(data0)
        elif (self.ret0[0] > self.p.high):
            if position0.size>0:
                self.sell(data0)

        if(self.ret1[0] < self.p.low):
            if cash > data1:
                self.buy(data1)
        elif (self.ret1[0] > self.p.high):
            if position1.size>0:
                self.sell(data1)

    def stop(self):
        pnl = round(self.broker.getvalue() - self.startcash, 2)
        print(' Pnl:{} High:{} Low:{} Period:{}'.format(
            pnl, self.p.high, self.p.low, self.p.period))

    def notify_fund(self, cash, value, fundvalue, shares):
        if DEBUG:
            print("notify_fund",cash, value, fundvalue, shares)
        

    def notify_trade(self,trade):
        if DEBUG:
            print("notify_trade",trade)


class DailySizer(bt.Sizer):
    def _getsizing(self, comminfo, cash, data, isbuy):
        if DEBUG:
            print("_getsizing", comminfo, cash, data[0], isbuy)
        position = self.strategy.getposition(data)
        if DEBUG:
            print("Postition", position)
        count = 0
        # if buying then buy using all the remaining cash
        # if selling only see the positive positions, if no position exist DO NOT SHORT
        if isbuy:
            count = int(cash/data)
            if DEBUG:
                print("Buying", count)
        else:
            count = position.size
            if count < 0:
                count = 0
            if DEBUG:
                print("Selling", count)
        #print(isbuy,count)
        return count


if IS_OPTIMIZE:
    cerebro = bt.Cerebro(maxcpus=1)
    cerebro.optstrategy(DStrategy, low=np.arange(-0.007, -0.002, 0.001),
                        high=np.arange(0.005, 0.012, 0.001),
                        period=np.arange(3, 12))
else:
    cerebro = bt.Cerebro(tz=0)
    cerebro.addstrategy(DStrategy)
    
cerebro.addsizer(DailySizer)
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharperatio')

store = alpaca_backtrader_api.AlpacaStore(paper=ALPACA_PAPER)

if IS_LIVE:
    broker = store.getbroker()  # or just alpaca_backtrader_api.AlpacaBroker()
    cerebro.setbroker(broker)
else:
    cerebro.broker.setcash(10000)

DataFactory = store.getdata  # or use alpaca_backtrader_api.AlpacaData
#DataFactory = alpaca_backtrader_api.AlpacaData  # or use alpaca_backtrader_api.AlpacaData

if IS_LIVE:
    data0 = DataFactory(
        dataname='MSFT',
        timeframe=bt.TimeFrame.TFrame("Days"))
    data1 = DataFactory(
        dataname='AAPL',
        timeframe=bt.TimeFrame.TFrame("Days"))
else:
    fm = pd.Timestamp('2019-10-04')
    to = pd.Timestamp('2019-12-18')
    data0 = DataFactory(
        dataname='MSFT',
        timeframe=bt.TimeFrame.TFrame("Days"),
        fromdate=fm,
        todate=to,
        historical=True)

    data1 = DataFactory(
        dataname='AAPL',
        timeframe=bt.TimeFrame.TFrame("Days"),
        fromdate=fm,
        todate=to,
        historical=True)


cerebro.adddata(data0)
cerebro.adddata(data1)

print(cerebro.broker.getcash())
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
stats = cerebro.run()
thestat = stats[0]
# print("After cerebro run stats",stats)
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
print('Analyzer sharperatio:', thestat.analyzers.sharperatio.get_analysis())

if not IS_OPTIMIZE:
    cerebro.plot()
