
import alpaca_trade_api as tradeapi
from pandas.tseries.offsets import DateOffset
import datetime
import pandas as pd

api = tradeapi.REST(key_id='PK8TJB4I5YZ4IRO6VVM8', secret_key='pzJIbG8itMk1KNMAYYgZ/ZVa4IogpHIMoKTzFB7r',base_url='https://paper-api.alpaca.markets', api_version='v2') # or use ENV Vars shown below

def get_avg_price(days=3,symbol='MSFT'):
    
    #TODO Implement market clock
    #Start date is current date and end date is 'days' before start date
    end_date = pd.Timestamp(datetime.date.today())
    start_date = end_date-DateOffset(days=3)
    end_date_iso = end_date.isoformat()
    start_date_iso = start_date.isoformat()
    bars = api.get_barset(symbol,timeframe='day',start=start_date_iso,end=end_date_iso,limit=3)
    length = len(bars[symbol])
    closed_end = bars[symbol][-1].c
    closed_start = bars[symbol][0].c
    perc_change = (closed_end-closed_start)/closed_start
    return perc_change

def main_func():
    
    account = api.get_account()
    cash = account.cash

    #Get positions
    print(api.list_positions())

    #Get list of all orders
    #print(api.list_orders())

    #print(api.get_barset('MSFT',timeframe='1D'))


    perc_change = get_avg_price(3,'MSFT')

    if perc_change < -0.005:
        bar = api.get_barset(symbols='MSFT',timeframe='min',limit=1)
        price = bar['MSFT'][0].c
        quantity = cash*0.5/price
        api.submit_order(symbol='MSFT',qty=1, side='buy',time_in_force='gtc',type='market')
    elif perc_change > 0.008:
        try:
            api.close_position(symbol='MSFT')
        except Exception as e:
            print(e)
            print("Error ocurred while closing position, maybe no open position exist?")


    print(perc_change)

if __name__ == '__main__':
     main_func()