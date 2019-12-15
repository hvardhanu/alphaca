
from pandas.tseries.offsets import DateOffset
import datetime
import pandas as pd
import BaseAlpha as BaseAlpha

def main_func():
    base = BaseAlpha.BaseAlpha()
    perc_change = base.get_avg_price(4, 'MSFT')
    strategy(base,'MSFT', perc_change, base)


def strategy(base, symbol="", perc_change=0, isTest=False):
    
    buying_power = base.get_buying_power()
    order_type = ""
    print("Percentage Change:",perc_change)

    if perc_change < -0.003:
        if isTest:
            print("Seems like a unit test is running")
            bar = base.api.get_barset(symbol, timeframe='day', limit=1)
        else:
            bar = base.api.get_barset(symbol, timeframe='min', limit=1)

        price = bar[symbol][0].c
        quantity = float(buying_power)/float(price)
        quantity = int(quantity)
        print("buying_power ", buying_power)
        order_type = "BOUGHT"
        base.place_order_market(symbol,quantity)
    elif perc_change > 0.011:
        base.close_position(symbol)
        order_type = "SOLD"
    return order_type

if __name__ == '__main__':
    main_func()
