
import alpaca_trade_api as tradeapi
from pandas.tseries.offsets import DateOffset
import datetime
import pandas as pd

api = tradeapi.REST(key_id='PK8TJB4I5YZ4IRO6VVM8', secret_key='pzJIbG8itMk1KNMAYYgZ/ZVa4IogpHIMoKTzFB7r',base_url='https://paper-api.alpaca.markets', api_version='v2') # or use ENV Vars shown below

def get_avg_price(days=3,symbol='MSFT'):
    
    #TODO Implement market clock
    #Start date is current date and end date is 'days' before start date
    end_date = pd.Timestamp(datetime.date.today())
    start_date = end_date-DateOffset(days=days)
    end_date_iso = end_date.isoformat()
    start_date_iso = start_date.isoformat()
    bars = api.get_barset(symbol,timeframe='day',start=start_date_iso,
                        end=end_date_iso,limit=days)
    #print(bars)
    closed_end = bars[symbol][-1].c
    closed_start = bars[symbol][0].c
    perc_change = (closed_end-closed_start)/closed_start
    return perc_change

def main_func():
     perc_change = get_avg_price(4,'MSFT')
     strategy('MSFT',perc_change)
    
def strategy(symbol="",perc_change=0,isTest=False):    
    account = api.get_account()
    buying_power = account.buying_power
    print(account.portfolio_value)

    #Get positions
    print(api.list_positions())
    order_type=""
    print(perc_change)

    if perc_change < -0.003:
        if isTest:
            print("Seems like a unit test is running")
            bar = api.get_barset(symbol,timeframe='day',limit=1)
        else:
            bar = api.get_barset(symbol,timeframe='min',limit=1)

        price = bar[symbol][0].c
        #print(type(buying_power))
        #print(type(price))
        quantity = float(buying_power)/float(price)
        quantity = int(quantity)
        print("buying_power ",buying_power)
        print("Number of stocks bought ",quantity)
        order_type="BOUGHT"
        api.submit_order(symbol=symbol,qty=quantity, side='buy',time_in_force='day',type='market')
    elif perc_change > 0.011:
        try:
            api.close_position(symbol=symbol)

            order_type="SOLD"
        except Exception as e:
            print(e)
            print("Error ocurred while closing position, maybe no open position exist?")
    return order_type

def cancelAllOrders():
    api.cancel_all_orders()

if __name__ == '__main__':
     main_func()