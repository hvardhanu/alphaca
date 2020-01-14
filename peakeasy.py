
from pandas.tseries.offsets import DateOffset
from datetime import datetime, timedelta
import pandas as pd
import BaseAlpha as BaseAlpha
import time
import numpy as np
from pytz import timezone
import argparse

"""
Peakasy Strategy
"""
parser = argparse.ArgumentParser(description='Peakeasy Strategy')
parser.add_argument("--istesting", default=False, type=bool, help="Are we just testing during non market hours?")
parser.add_argument("stock", type=str, help="Which Stock?")

args = parser.parse_args()

TOTAL_BARS_TO_GET=28
IS_OFFLINE_TESTING = args.istesting
IS_BACKTEST = False
DAYS_TO_BACKTEST = 60 
base = BaseAlpha.BaseAlpha('peakeasy')

def main_init(date):

    if date == '':
        date = datetime.today()
    print("Hello! executing on:", date)

    IS_MARKET_OPEN,timestamp = base.isMarketOpen()
    # exit if we are not testing and market is not open
    if (not IS_OFFLINE_TESTING) and (not IS_MARKET_OPEN):
        print("Not testing and the market is closed, no business here, so exiting!")
        return

    #stockfile = base.getPickle()

    stock = args.stock

    period = base.getPeriod(stock)
    stoplossFactor = base.getStoploss(stock)
    cash_lane = base.getCashLane(stock)

    print("Running for {} Period:{} StoplossFactor:{}, CashLane:{}".format(stock,period,stoplossFactor,cash_lane))
    #Always get TOTAL_BARS_TO_GET bars
    df_data = base.getArrayFromBars(stock, TOTAL_BARS_TO_GET,date)
    print(df_data)

    rsi = base.getRSI(df_data['close'],14)
    print("RSI is:",rsi)
    latestPrice = float(base.getCurrentPrice(stock))

    buying_power = float(base.get_buying_power())
    
    #checking if cashlane for stock is lower than buying power, if not then use whatever buying power is left
    if buying_power>cash_lane:
        buying_power=cash_lane
    buy_quantity = 0

    if latestPrice > 0:
        #Reducing by one to ensure we have sufficient cash in case of minor price increase
        buy_quantity = int(buying_power/latestPrice)-1
    else:
        print("latestPrice is {},setting buy quantity to 0".format(latestPrice))

    
    if not IS_BACKTEST:
        date = timestamp.strftime("%Y-%m-%d")
    
    #ar_close = np.array(df_data['close'][14:])
    start_bar = TOTAL_BARS_TO_GET-period
    ar_close = np.array(df_data['close'][start_bar:])
    print(ar_close)
    isPeak = base.isPeak(ar_close)
    isTrough = base.isTrough(ar_close)
    

    print("Price{}, Is Peak:{}, Is Trough:{}".format(
        latestPrice, isPeak, isTrough))

    if isPeak:
        # sell (close position) but first cancel any pending stoploss orders
        try:
            base.cancelStopLoss(stock)
        except Exception as e:
            print("Exception while calling cancelStopLoss",e)
            #Keep going and try to close position even if stop loss didnt cancel
        try:
            base.closePositionStock(stock)
        except Exception as e:
            print("Exception while trying to Close postions, we will now try to place a stoploss",e)
            # Now we failed to close postion lets try to set up a stoploss
            position=base.getPosition(stock)
            if int(position.qty>0):
                base.orderGTCStopLoss(stock,position.qty,latestPrice*stoplossFactor)
        
    if isTrough and rsi>30 and rsi<70:
        # place a buy order and a stop loss order,
        # cancel/liquidate buy if stop loss is not placed
        if buy_quantity>0:
            base.placeBuyWithStop(stock,buy_quantity,stoplossFactor)
        else:
            print("buy_quantity<=0, no buy trade placed")
    
    print("Adios for today!")

def backTest():
    base.enableBackTest(10000)
    now = datetime.now(timezone('EST'))
    beginning = now - timedelta(days=DAYS_TO_BACKTEST) 
    # The calendars API will let us skip over market holidays and handle early
    # market closures during our backtesting window.
    calendars = base.api.get_calendar(
        start=beginning.strftime("%Y-%m-%d"),
        end=now.strftime("%Y-%m-%d")
    ) 
    print("Starting Portfolio {}".format(base.btPortfolio))
    for calendar in calendars:
        print(calendar)
        #adding 20 hours to make it EOD
        main_init(calendar.date+timedelta(hours=20))
    print("Ending Portfolio {}".format(base.btPortfolio))




if __name__ == '__main__':
    if IS_BACKTEST:
        backTest()
    else:
        main_init('')
