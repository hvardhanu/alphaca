
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
from backtrader.plot.scheme import PlotScheme
import argparse


#---Arg Parsing---
parser = argparse.ArgumentParser(description='Peaks and Troughs Strategy')
parser.add_argument("--ispaper", default=True, type=bool, help="Do we want to use Paper API?")
parser.add_argument("--islive", default=False, type=bool, help="Run on Live? Really?")
parser.add_argument("--istrend", default=False, type=bool, help="Use trend checks?")
parser.add_argument("--isopt", default=False, type=bool, help="Should we run optimize?")
parser.add_argument("--showplot", default=False, type=bool, help="Should we show plot?")
parser.add_argument("--iscsv", default=False, type=bool, help="Print Results to CSV?")
parser.add_argument("--isallin", default=False, type=bool, help="All in on Cash?")
parser.add_argument("--stock", default="SPY", type=str, help="Which Symbol? SPY is default")
parser.add_argument("--start", default="2019-01-01", type=str, help="Start Date. 2019-01-30 is default")
parser.add_argument("--end", default="2020-01-04", type=str, help="End Date. '2020-01-04' is default")

args = parser.parse_args()
ALPACA_PAPER = args.ispaper
IS_LIVE = args.islive
IS_OPTIMIZE = args.isopt
ALL_IN = args.isallin
SHOW_PLOT = args.showplot
IS_CSV = args.iscsv
IS_TREND = args.istrend
# Optimization history for only long and close
# Stock Start       End         Optimal   Period Return
# GM    2018-01-26 2018-12-18   6
# S&P   2018-01-26 2019-12-18   13        15%
# MSFT  2018-01-26 2019-12-18   19        50%
# MSFT  2018-01-26 2019-12-18   20        35% (without trend checks)
# GM    2018-01-26 2019-12-18   7        -1%
# GM    2018-01-26 2019-12-18   12        20% (Without trend checks, without RSI Check)
# DBX   2018-03-26 2019-12-18   6         56% (Without trend checks, without RSI Check)
# DBX   2018-06-01 2019-12-25   X         X% (Without trend checks,  without RSI Check)
# IDT **2019-01-30 2020-01-04    27        31% (without trend checks, without RSI Check)
# Added Check for RSI, after looking at PCYG example below
# PCYG  2019-01-30 2020-01-04    27        -60% (without trend checks)
# PCYG  2019-01-30 2020-01-04    27        -15% (without trend checks WITH RSI Check)
# DBX   2018-03-26 2019-12-18   6         56% (Without trend checks, With RSI Check)
# Added ATR Stoploss
# DBX   2018-03-26 2019-12-18   27         -15% (Without trend checks, With RSI Check, Stoploss 1xATR)

fromdate = pd.Timestamp(args.start)
todate =  pd.Timestamp(args.end)
stck = args.stock

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
    dist = len(prices)
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
    dist = len(prices)
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
def getTrend(sma):
    dist = 3
    lastPrice = sma[-1]
    firstPrice = sma[-dist+1]
    slope = (lastPrice-firstPrice)/3
    return slope

class SmaCross(bt.Strategy):

    params = (('period', 14),('stoploss',4),('alloc',0.05),('lossTolerance',0.05))
 
    def __init__(self):
        self.openStopLoss = []
        self.startcash = cerebro.broker.getcash()
        #get SMA
        self.sma = bt.ind.ExponentialMovingAverage(period=self.p.period)
        #For plotting RSI
        self.rsi = bt.ind.RelativeStrengthIndex()
        #ATR
        self.atr = bt.ind.AverageTrueRange()
        self.isPeak = bt.ind.ApplyN( self.sma,func=isPeak, period=self.p.period)
        self.isTrough = bt.ind.ApplyN( self.sma,func=isTrough, period=self.p.period)

    def notify_cashvalue(init, cash, value):
        #print("Cash:",cash," Pf Value:",value)
        pass

    def notify_trade(init, trade):    
        if not IS_OPTIMIZE:
            print("Trade Ref:{} Trade ID:{} IsOpen:{} IsClosed:{} Size:{} DtOpen:{} DtClosed:{}, Pnl:{}".format(
                trade.ref, trade.tradeid,trade.isopen,trade.isclosed,trade.size,datetime.datetime.fromtimestamp(trade.dtopen),
                datetime.datetime.fromtimestamp(trade.dtclose),trade.pnl))
        pass

    def notify_order(init, order):
        if order.getstatusname()=='Margin':
            print("Order in PENDING State ###")
        if not IS_OPTIMIZE:
            print("Order Ref:{} Status:{} Size:{} Type:{} ExType:{}.".format(
                order.ref,order.getstatusname(),order.size,order.ordtypename(),order.getordername()))
        pass

    def next(self):
        dt = self.datetime.datetime(ago=0)
        cash = self.broker.getcash()
        rsi = self.rsi # Get RSI
        atr = self.atr # We will use ATR to set a Stoploss
        # if the IS_TREND flag is set , make the isUptrend flag have effect 
        #i.e. have value true or false based on slope, if flag not set then just keep it true
        isUptrend = False
        if IS_TREND:
            slope = (self.sma[-1]-self.sma[-3])/3 # calculate the slop
            #print("Slope",slope)
            if slope > 0:
                isUptrend = True
        else:
            isUptrend = True

        stoplossdiff = atr*self.p.stoploss
        #stoplossdiff = data0*0.1
        if not IS_OPTIMIZE:
            print("Day:{}, Cash:{} Price:{}, Is Peak:{}, Is Trough:{}".format(dt,cash,self.data0[0],self.isPeak[0],self.isTrough[0]))
        #print(self.broker.g)
        #if self.isTrough and rsi>30 and rsi<70 and isUptrend: # Do not buy if RSI<30 (oversold) and >70 (already overbought)
        if self.isTrough and isUptrend: # Do not buy if RSI<30 (oversold) and >70 (already overbought)    
            if ALL_IN:
                # Setting 90% as the cash that can be utilized
                st_size = int((cash*self.p.alloc)/(data0[0]))
            else:
                #find the max loss we can tolerate and calculate size using stoploss diff
                max_size = int((cash*self.p.alloc)/(data0[0]))
                max_loss = cash*self.p.lossTolerance
                st_size = int(max_loss/stoplossdiff)
                if st_size>max_size:
                    st_size=max_size
            
            if st_size>0:
                self.buy(exectype=bt.Order.Market,size=st_size)
                short_ord = self.sell(size=st_size,price=(data0[0]-stoplossdiff),exectype=bt.Order.Stop)
                self.openStopLoss.append(short_ord)
            else:
                #print("Not placing a 0 size order")
                pass
        if self.isPeak:
            for ordr in self.openStopLoss:
                #print("canceling Stoploss order")
                self.cancel(ordr)
            self.openStopLoss = []
            order = self.close(valid=0)
            #print("close",order)

    def stop(self):
        ta = self.analyzers.ta.get_analysis()
        # sharpe = self.analyzers.shr.get_analysis()
        # print(sharpe.sharperatio)
        printTradeAnalysis(ta,self.p.period,self.p.stoploss)

def printTradeAnalysis(analyzer,period,stoploss):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    #Get the results we are interested in
    total_open = analyzer.total.open
    total_closed = analyzer.total.closed
    total_won = analyzer.won.total
    total_lost = analyzer.lost.total
    win_streak = analyzer.streak.won.longest
    lose_streak = analyzer.streak.lost.longest
    won_avg = analyzer.won.pnl.average
    lost_avg = analyzer.lost.pnl.average
    pnl_net = round(analyzer.pnl.net.total,2)
    strike_rate = (total_won / total_closed) * 100
    #Designate the rows
    r1 = map(lambda x: str(round(x,2)),[total_open, total_closed,total_won,total_lost,won_avg,lost_avg,strike_rate, win_streak, lose_streak, pnl_net,period,stoploss])
    #Check which set of headers is the longest.
    header_length = 12
    #Print the rows
    if IS_CSV:
        row_format ="{}," * (header_length + 1)
    else:
        row_format ="{:<15}" * (header_length + 1)
    print(row_format.format('',*r1))

cerebro = bt.Cerebro()
if IS_OPTIMIZE:
    cerebro = bt.Cerebro(maxcpus=1)
    cerebro.optstrategy(SmaCross, period=np.arange(15, 55),stoploss=np.arange(3,3.5,0.5))
else:
    cerebro = bt.Cerebro()
    cerebro.addstrategy(SmaCross)

#cerebro.addsizer(bt.sizers.PercentSizer, percents=100)
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='shr')
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='ta')

store = alpaca_backtrader_api.AlpacaStore(
    paper=ALPACA_PAPER
)

if IS_LIVE:
    broker = store.getbroker()  # or just alpaca_backtrader_api.AlpacaBroker()
    cerebro.setbroker(broker)
else:
    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(commission=0.0)
    cerebro.broker.set_coc(True)

DataFactory = store.getdata  # or use alpaca_backtrader_api.AlpacaData

if IS_LIVE:
    data0 = DataFactory(
        dataname='AAPL',
        timeframe=bt.TimeFrame.TFrame("Days"))
else:
    data0 = DataFactory(
        dataname=stck,
        timeframe=bt.TimeFrame.TFrame("Days"),
        fromdate=fromdate,
        todate=todate,
        historical=True)

cerebro.adddata(data0)
#cerebro.replaydata(data0)

if not IS_CSV:
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost', 'Won Avg', 'Lost Avg','Strike Rate','Win Streak', 'Losing Streak', 'PnL Net','Period','Stoploss']
header_length=len(h1)
if IS_CSV:
    row_format ="{}," * (header_length + 1)
else:
    row_format ="{:<15}" * (header_length + 1)
if IS_OPTIMIZE:
    print(row_format.format('',*h1))

stats = cerebro.run()

if not IS_OPTIMIZE:
    print(row_format.format('',*h1))
thestat = stats[0]
if not IS_CSV:
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())



if (not IS_OPTIMIZE) and SHOW_PLOT:
    cerebro.plot(style='candle')
    pass
