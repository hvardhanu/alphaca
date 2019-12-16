
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
IS_LIVE = True
IS_OPTIMIZE = False

class SmaCross(bt.Strategy):

  params = (('low',-0.005),('high',0.01),('period',10))

  def __init__(self):
    # print("Init")
    # print(self.p.low)
    self.startcash=cerebro.broker.getcash()
    self.pctCh = bt.ind.PctChange(period=self.p.period)
    #self.longterm_ind = bt.ind.PctChange(period=15)
    
  
  def next(self):
    #print("In Next",self.pctCh[0])
    #print(type(self.pctCh[0]))
    print(self.pctCh[0] < self.p.low)
    if (self.pctCh[0] < self.p.low):
      print("Buy")
      self.buy()
    if (self.pctCh[0] > self.p.high):
      print("close")
      self.close()
  def stop(self):
    pnl = round(self.broker.getvalue() - self.startcash,2)
    print(' Period:{} Low: {} High:{} Final PnL: {}'.format(
            self.p.period, self.p.low, self.p.high , pnl))

  
  # def notify_fund(self, cash, value, fundvalue, shares):
  #     print(cash, value, fundvalue, shares)
      


cerebro = bt.Cerebro()
if IS_OPTIMIZE:
  cerebro = bt.Cerebro(maxcpus=1)
  cerebro.optstrategy(SmaCross,low=np.arange(-0.007,-0.002,0.001),
                              high=np.arange(0.005,0.012,0.001),
                              period=np.arange(3,12))
else:
  cerebro = bt.Cerebro()
  cerebro.addstrategy(SmaCross)

cerebro.addsizer(bt.sizers.PercentSizer, percents=20)
#cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharperatio')

store = alpaca_backtrader_api.AlpacaStore(
    paper=ALPACA_PAPER
)

if IS_LIVE:
  broker = store.getbroker()  # or just alpaca_backtrader_api.AlpacaBroker()
  cerebro.setbroker(broker)
else:
  cerebro.broker.setcash(1000)
  #cerebro.broker.setcommission(commission=0.0)

DataFactory = store.getdata  # or use alpaca_backtrader_api.AlpacaData

if IS_LIVE:
  data0 = DataFactory(
      dataname='AAPL',
      timeframe=bt.TimeFrame.TFrame("Days"))
else:
   data0 = DataFactory(
      dataname='AAPL',
      timeframe=bt.TimeFrame.TFrame("Days"),
      fromdate=pd.Timestamp('2018-02-26'),
      todate=pd.Timestamp('2019-04-18'),
      historical=True)

cerebro.adddata(data0)

print(cerebro.broker.getcash())
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
stats = cerebro.run()
thestat =stats[0]
# print("After cerebro run stats",stats)
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
#print('Analyzer sharperatio:', thestat.analyzers.sharperatio.get_analysis())

if not IS_OPTIMIZE:
  cerebro.plot()