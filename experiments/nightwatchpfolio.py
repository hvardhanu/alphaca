
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
IS_OPTIMIZE = True

class SmaCross(bt.Strategy):

  params = (('equity',0.5))

  def __init__(self):
    # print("Init")
    # print(self.p.low)
    self.stock1 = self.datas[0]
    self.stock2 = self.datas[1]
    self.startcash=cerebro.broker.getcash()
    
  
  def next(self):
    #print(self.p.low)
    self.order_target_percent(self.stock1, target=self.params.equity)
    self.order_target_percent(self.stock2, target=(1 - self.params.equity))

  def stop(self):
    pnl = round(self.broker.getvalue() - self.startcash,2)
    print(' Pnl:{}'.format(pnl))

  
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

#cerebro.addsizer(bt.sizers.PercentSizer, percents=20)
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharperatio')

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
   fm=pd.Timestamp('2018-02-26')
   to=pd.Timestamp('2019-04-18')
   pf = ['AAPL','MSFT']
   data0 = DataFactory(
      dataname=pf,
      timeframe=bt.TimeFrame.TFrame("Days"),
      fromdate=fm,
      todate=to,
      historical=True)
  #  data1 = DataFactory(
  #     dataname=pf[1],
  #     timeframe=bt.TimeFrame.TFrame("Days"),
  #     fromdate=fm,
  #     todate=to,
  #     historical=True)

cerebro.adddata(data0)
#cerebro.adddata(data1)

print(cerebro.broker.getcash())
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
stats = cerebro.run()
thestat =stats[0]
# print("After cerebro run stats",stats)
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
print('Analyzer sharperatio:', thestat.analyzers.sharperatio.get_analysis())

if not IS_OPTIMIZE:
  cerebro.plot()