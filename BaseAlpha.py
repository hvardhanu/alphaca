import numpy as numpy
import pandas as pd
from pandas.tseries.offsets import DateOffset
import datetime
import alpaca_trade_api as tradeapi


class BaseAlpha:
    def __init__(self):
        api = tradeapi.REST(key_id='PK714C2Y2AKEKG1GJHAQ',
                    secret_key='NwgIb/ZhtYWvEyulzuv6BfWnQJk0iqmxSnO/snKv',
                    base_url='https://paper-api.alpaca.markets',
                    api_version='v2')  # or use ENV Vars shown below
        self.api = api

    def cancel_all_ord(self):
        try:
            self.api.cancel_all_orders()
            print("** Canceling all orders **")
        except  tradeapi.rest.APIError as e:
            print("Error in cancel_all_ord - ", e)

    def place_order_market(self, symbol, quantity):
        try:
            self.api.submit_order(symbol=symbol,
                                  qty=quantity, side='buy',
                                  time_in_force='day',
                                  type='market')
            
            print("Placed order ", symbol," ", quantity)
        except tradeapi.rest.APIError as e:
            print("Error in place_order_market - ", e)
    
    def close_position(self,symbol):
        try:
            self.api.close_position(symbol=symbol)
            print("Closing position for ",symbol)
        except tradeapi.rest.APIError as e:
            print(e)
            print("Error ocurred while closing position, maybe no open position exist?")

    def get_buying_power(self):
        account = self.api.get_account()
        return account.buying_power

    def get_avg_price(self, days=0, symbol=''):

        # TODO Implement market clock
        # Start date is current date and end date is 'days' before start date
        end_date = pd.Timestamp(datetime.date.today())
        start_date = end_date-DateOffset(days=days)
        end_date_iso = end_date.isoformat()
        start_date_iso = start_date.isoformat()
        try:
            bars = self.api.get_barset(symbol, timeframe='day', start=start_date_iso,
                                       end=end_date_iso, limit=days)
        except tradeapi.rest.APIError as e:
            print("Error in get_avg_price while getting bars- ", e)
        # print(bars)
        closed_end = bars[symbol][-1].c
        closed_start = bars[symbol][0].c
        perc_change = (closed_end-closed_start)/closed_start
        return perc_change
