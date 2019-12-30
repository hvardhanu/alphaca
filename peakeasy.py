
from pandas.tseries.offsets import DateOffset
from datetime import datetime, timedelta
import pandas as pd
import BaseAlpha as BaseAlpha
import time
import numpy as np
from pytz import timezone


IS_OFFLINE_TESTING = True
IS_BACKTEST = True
DAYS_TO_BACKTEST = 90 
base = BaseAlpha.BaseAlpha()

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

    period = 6
    stoplossFactor = 0.85
    stock = 'MSFT'
    df_data = base.getArrayFromBars(stock, period,date)
    print(df_data)

    latestPrice = float(base.getCurrentPrice(stock))
    #latestPrice = 190
    buying_power = float(base.get_buying_power())
    buy_quantity = 0

    if latestPrice > 0:
        buy_quantity = int(buying_power/latestPrice)
    else:
        print("latestPrice is {},setting buy quantity to 0".format(latestPrice))

    
    if not IS_BACKTEST:
        # getting one less period as we will add an extra i.e. today's price later
        date = timestamp.strftime("%Y-%m-%d")
        period = period-1
    
    ar_close = np.array(df_data['close'])
    # adding the latest price as the getArrayFromBars does not have today's price
    if not IS_BACKTEST:
        ar_close = np.append(ar_close, latestPrice)

    print(ar_close)
    isPeak = base.isPeak(ar_close)
    isTrough = base.isTrough(ar_close)
    
    #TODO Comment
    # isTrough = True
    # isPeak = False

    print("Price{}, Is Peak:{}, Is Trough:{}".format(
        latestPrice, isPeak, isTrough))

    if isPeak:
        # sell (close position) but first cancel any pending stoploss orders
        base.cancelStopLoss(stock)
        base.closePositionStock(stock)

    if isTrough:
        # place a buy order and a stop loss order,
        # cancel/liquidate buy if stop loss is not placed
        base.placeBuyWithStop(stock,buy_quantity,stoplossFactor)
    
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
        main_init(calendar.date)
    print("Ending Portfolio {}".format(base.btPortfolio))




if __name__ == '__main__':
    if IS_BACKTEST:
        backTest()
    else:
        main_init('')
