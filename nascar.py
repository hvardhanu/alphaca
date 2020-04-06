from pandas.tseries.offsets import DateOffset
from datetime import datetime, timedelta
import pandas as pd
import BaseAlpha as base
import time
import numpy as np
from pytz import timezone
import argparse
import http.client
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
#parser.add_argument("--stock", type=str, help="Which Stock?")
parser.add_argument("--period", type=int, help="What's the period?")

base = base.BaseAlpha('Nascar')
args = parser.parse_args()
period = args.period

stock_list=['IT','NKE','DIS','F','GM','MSFT','SBUX','AMD','CRM','DOCU','FB','UPS','AMGN','DAL',
'USO','DBX','GLD','XLK','XLY','XLP','XRT','XLF','XLI','VXX','LQD','AGG','TLT','EMB','MUB','IEF',
'XLE','XLV','XLB','XLU','UUP','FXI','VGK','GDX','INDA','EWJ','RSX','SPY']
ifttt_req=''
for stock in stock_list:
    stock_bars = base.api.get_barset(stock, timeframe='day', limit=period+2)
    stock_df=stock_bars.df[stock]

    speed_latest = base.getSpeedDF(stock_df['close'], period)
    speed_last = base.getSpeedDF(stock_df['close'][:-1], period)

    #print(speed_latest)
    #print(speed_last)

    if speed_last<0 and speed_latest>=0:
        print('BUY',stock)
        ifttt_req=ifttt_req+','+stock

    
    time.sleep(1)

#now send the request to IFTTT
if ifttt_req!='':
    conn = http.client.HTTPSConnection("maker.ifttt.com")
    conn.request("POST","/trigger/nascar_list/with/key/ehSoX21int_FlYv5fF9Tg?value1="+ifttt_req)







