from pandas.tseries.offsets import DateOffset
from datetime import datetime, timedelta
import pandas as pd
import BaseAlpha as base
import time
import numpy as np
from pytz import timezone
import argparse
import http.client
from tinydb import TinyDB, Query
conn = http.client.HTTPSConnection("localhost", 8080)

"""
Peakasy Strategy
calculate today_speed, yesterday_speed over X number of days 
calculate ATR over Y number of days
if today_speed > 0 and yesterday_speed<0 => BUY
if today_speed > 0  set stop loss - strategy.exit("exit", "BUY", stop = close-atr*low_factor)
"""
parser = argparse.ArgumentParser(description='Nascar')
parser.add_argument("--istesting", default=False, type=bool, help="Are we just testing during non market hours?")
parser.add_argument("--period", type=int, default=15, help="What's the period? Default 15")
parser.add_argument("--buyPercentage", type=float, default=0.05, help="What percentage of the portfolio should be bought in a transaction? Default 0.05")
parser.add_argument("--stoplossFactor", type=int, default=3, help="What is the stoploss, what is the multiple of ATR to be used for stoploss? Default 3")
parser.add_argument("--method", type=str, help="Is this screen, buy, adjust?")

base = base.BaseAlpha('Nascar')
args = parser.parse_args()
period = args.period
method = args.method
buy_percentage=args.buyPercentage
stoploss_factor=args.stoplossFactor
date = datetime.today()
stock_list=['IT','NKE','DIS','F','GM','MSFT','SBUX','AMD','CRM','DOCU','FB','UPS','AMGN','DAL',
'USO','DBX','GLD','XLK','XLY','XLP','XRT','XLF','XLI','VXX','LQD','AGG','TLT','EMB','MUB','IEF',
'XLE','XLV','XLB','XLU','UUP','FXI','VGK','GDX','INDA','EWJ','RSX','SPY']

db = base.db
#screens stock, sends a IFTTT alert, adds the stocks to DB for buy to "buy"
def screen():
    ifttt_req=''
    stock_list_out=[]
    buyQ=Query()
    #Todo
    print("Hello! executing NASCAR screener on:", date)

    for stock in stock_list:
        stock_bars = base.api.get_barset(stock, timeframe='day', limit=period+2)
        stock_df=stock_bars.df[stock]

        speed_latest = base.getSpeedDF(stock_df['close'], period)
        speed_last = base.getSpeedDF(stock_df['close'][:-1], period)

        #print(speed_latest)
        #print(speed_last)

        if speed_last<0 and speed_latest>=0:
            print('BUY',stock)
            stock_list_out.append(stock)
            #Get ATR
            atr=base.getATR(stock_df['high'],stock_df['low'],stock_df['close'],period)
            ifttt_req=ifttt_req+','+stock+'-ATR-'+str(atr)

        
        time.sleep(1)
    
    db.upsert({'type':'buy','stocks': stock_list_out,'date':str(date)},buyQ.type=='buy')
    db.insert({'type':'record','stocks': stock_list_out,'date':str(date)})

    #now send the request to IFTTT
    if ifttt_req!='':
        conn = http.client.HTTPSConnection("maker.ifttt.com")
        conn.request("POST","/trigger/nascar_list/with/key/ehSoX21int_FlYv5fF9Tg?value1="+ifttt_req)

# Picks the buy stocks for the day,
# checks if already bought, 
# if not then buys them, 
# set the initial stoploss
def buy():
    print("Hello! executing NASCAR buy on:", date) 
    IS_MARKET_OPEN,timestamp = base.isMarketOpen()
    if not IS_MARKET_OPEN:
        print("The market is closed, no business here, so exiting!")
        return 
    # Picks the buy stocks for the day,
    buyQ=Query()
    record=db.get(buyQ.type=='buy')
    buy_stocks=record['stocks']
    account = base.api.get_account()
    #checks if already bought
    #GET open postions - retrieve stocks
    buy_stocks=base.getNotOverlappingStocks(buy_stocks)
    print("List of BUY candidates",buy_stocks)
    
    for stock in buy_stocks:
        #caculate number of stocks
        #buy
        try:
            #price=base.getCurrentPrice(stock)
            stock_bars = base.api.get_barset(stock, timeframe='day', limit=period+2)
            stock_df=stock_bars.df[stock]
            price=float(stock_df['close'][-1])
            atr=base.getATR(stock_df['high'],stock_df['low'],stock_df['close'],period)
            #Willing to lose buy_percentage of the portfolio, with a stoploss of price-atr*stoploss_factor
            stop_price=price-atr*stoploss_factor
            buy_sizing=float(account.portfolio_value)*buy_percentage
            number_of_stocks=base.calculatePositionSizing(buy_sizing,price,stop_price)
            if float(account.buying_power)>=buy_sizing:
                #base.api.submit_order(stock,number_of_stocks,side='buy',type='market',time_in_force='gtc',order_class='oto',stop_loss=dict(stop_price=stop_price),client_order_id='nascar-'+stock+'-stop')
                stop_order_id = base.placeBuyWithStop(stock,number_of_stocks,atr*stoploss_factor)
                if stop_order_id !=False:
                    qry=Query()
                    base.db.upsert({'type':stock+'-id','id':stop_order_id},qry.type==stock+'-id')
                    print(number_of_stocks,"units of",stock,"bought")
            else:
                print("Lack of buying power for", stock, "buying power is", account.buying_power)
            time.sleep(0.5)
        except Exception as e:
            print("Error in BUY",e)
       

# # Picks up the positions from the portfolio and re-sets the stop losses
def adjust():
    print("Hello! executing NASCAR adjust on:", date) 
    IS_MARKET_OPEN,timestamp = base.isMarketOpen()
    if not IS_MARKET_OPEN:
        print(timestamp,"The market is closed, no business here, so exiting!")
        return 

    # Get positions from the portfolio
    list_positions = base.api.list_positions()
    for position in list_positions: 
    # Adjust each position if speed
        try:
            stock = position.symbol
            stock_bars = base.api.get_barset(stock, timeframe='day', limit=period+2)
            stock_df=stock_bars.df[stock]
            atr=base.getATR(stock_df['high'],stock_df['low'],stock_df['close'],period)
            speed_latest = base.getSpeedDF(stock_df['close'], period)
            if speed_latest>0:
                price=stock_df['close'][-1]
                stop_price=price-atr*stoploss_factor
                qry = Query()
                rec = base.db.get(qry.type==stock+'-id')
                clOrderId=rec['id']
                #order = base.api.get_order(clOrderId)
                base.api.replace_order(stop_price=stop_price,order_id=clOrderId)
                print("Speed is",speed_latest,"&",stock,"Stoploss IS Updated")
            else:
                print("Speed is",speed_latest,"&",stock,"Stoploss NOT Updated")
            time.sleep(0.5)
        except Exception as e:
                print("Error in ADJUST",e)


if __name__ == '__main__':
    if method=='screen':
        screen()
    elif method=='buy':
        buy()
    elif method == 'adjust':
        adjust()
    else:
        pass
