
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime

# The above could be sent to an independent module
import alpaca_backtrader_api
import backtrader as bt

import pandas as pd


ALPACA_API_KEY = "PK8TJB4I5YZ4IRO6VVM8"
ALPACA_SECRET_KEY = "pzJIbG8itMk1KNMAYYgZ/ZVa4IogpHIMoKTzFB7r"
ALPACA_PAPER = True

class SmaCross(bt.SignalStrategy):
  def __init__(self):
    sma1, sma2 = bt.ind.SMA(period=10), bt.ind.SMA(period=30)
    crossover = bt.ind.CrossOver(sma1, sma2)
    self.signal_add(bt.SIGNAL_LONG, crossover)


cerebro = bt.Cerebro()
cerebro.addstrategy(SmaCross)
cerebro.broker.setcash(100000)
cerebro.broker.setcommission(commission=0.0)
cerebro.addsizer(bt.sizers.PercentSizer, percents=20)

store = alpaca_backtrader_api.AlpacaStore(
    key_id=ALPACA_API_KEY,
    secret_key=ALPACA_SECRET_KEY,
    paper=ALPACA_PAPER
)

if not ALPACA_PAPER:
  broker = store.getbroker()  # or just alpaca_backtrader_api.AlpacaBroker()
  cerebro.setbroker(broker)

DataFactory = store.getdata  # or use alpaca_backtrader_api.AlpacaData
data0 = DataFactory(
    dataname='AAPL',
    timeframe=bt.TimeFrame.TFrame("Minutes"),
    fromdate=pd.Timestamp('2018-11-15'),
    todate=pd.Timestamp('2018-11-17'),
    historical=True)
cerebro.adddata(data0)

print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.run()
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.plot()