import talib
import numpy as np
import pandas as pd
from pandas.tseries.offsets import DateOffset
import datetime
import alpaca_trade_api as tradeapi
from scipy.signal import find_peaks
import pickle
import time
from tinydb import TinyDB, Query
import pathlib


class BaseAlpha:

    api_time_format = '%Y-%m-%dT%H:%M:%S.%f-04:00'
    params = {'backtest': False}

    def __init__(self, strategy):
        api = tradeapi.REST(key_id='PK714C2Y2AKEKG1GJHAQ',
                            secret_key='NwgIb/ZhtYWvEyulzuv6BfWnQJk0iqmxSnO/snKv',
                            base_url='https://paper-api.alpaca.markets',
                            api_version='v2')  # or use ENV Vars shown below
        self.api = api
        self.backtest = False
        #getting the path of the current file, where the DB will be stored
        path = pathlib.Path(__file__).parent.absolute()
        db_path = str(path)+'/'+strategy+'.json'
        print("DB PATH",db_path)
        self.db = TinyDB(db_path)

    def getCashLane(self, stock):
        
        try:
            qry = Query()
            cash_lanes_rec = self.db.search(qry.type == 'cashlanes')
            cash_lane = cash_lanes_rec[0][stock]
            return float(cash_lane)
        except Exception as e:
            print("Error in getCashLane",e)
            return 0
        
     
    def getStocks(self):
        final_stocks=[]
        qry = Query()
        rec = self.db.search(qry.type == 'cashlanes')
        stocks = rec[0]
        for elem in stocks:
            if elem != 'type':
                final_stocks.append(elem)
        return final_stocks

    def getPeriod(self, stock):
        try:
            qry = Query()
            period_rec = self.db.search(qry.type == 'periods')
            period = period_rec[0][stock]
            return int(period)
        except Exception as e:
            print("Error in getPeriod",e)
            return 0

     
    def getStoploss(self, stock):
        try:
            qry = Query()
            stoploss_rec = self.db.search(qry.type == 'stoploss')
            stoploss = stoploss_rec[0][stock]
            return float(stoploss)
        except Exception as e:
            print("Error in getStoploss",e)
            return 0

    def enableBackTest(self, cash):
        self.backtest = True
        self.cash = cash
        self.btPrice = 0
        self.btStopLossPrice = 0
        self.btQty = 0
        self.btPortfolio = cash

    def placeBuyWithStop(self, stock, buy_quantity, stoplossFactor,stoploss_order_id="default_orderID"):
        try:
            buy_order = self.api.submit_order(symbol=stock,
                                              qty=buy_quantity, side='buy',
                                              time_in_force='day',
                                              type='market')
            print("Buy order placed", buy_order)
        except Exception as e:
            print("Exception while creating order:", e)
            return False

        time.sleep(1)

        try:
            status = ""
            counter = 0
            # Wait for order to get filled, try 5 times
            while (status != "filled") and counter < 5:
                buy_order = self.api.get_order(buy_order.id)
                status = buy_order.status
                counter = counter+1
                print("Wating for buy order to be filled, try {}".format(counter))
                time.sleep(1)

            # If not filled the foolowing line will raise exception
            if status != "filled":
                raise Exception("Waited for 5 seconds but order did not fill")

            stop_qty = int(buy_order.filled_qty)
            filled_price = float(buy_order.filled_avg_price)
            stop_price = filled_price-stoplossFactor
                        
            self.orderGTCStopLoss(stock, stop_qty, stop_price,stoploss_order_id)


            return True

        except Exception as e:
            print(
                "Error while placing matching stop order with Buy, cancelling buy order:", buy_order.id, e)
            try:
                self.api.cancel_order(buy_order.id)
            except Exception as ex:
                print("Error while cancelling buy order,closing positions", ex)
                self.api.close_position(stock)
            return False

    def getOrder(self, order_id):
        order = self.api.get_order(order_id)
        return order

    def orderGTCStopLoss(self, stock, qty, price,stoploss_order_id):
        stop_order = self.api.submit_order(
            symbol=stock, qty=qty, side="sell", type="stop", time_in_force="gtc", stop_price=price,client_order_id=stoploss_order_id)
        print("Stop order placed", stop_order)
       
    def closePositionStock(self, stock):
        #Bt#
        if self.backtest:
            self.cash = self.cash+self.btPrice*self.btQty
            print("Closing Position, sold", self.btQty)
            self.btQty = 0
            return
        ##
        # TODO change the logic, retrieve the order and calculate
        # the post cash, bug: https://github.com/alpacahq/alpaca-trade-api-python/issues/136
        try:
            pre_cash = self.get_buying_power()
        except Exception as e:
            print(e)

        self.api.close_position(stock)
        print("Closed all positions in", stock)

        try:
            time.sleep(1)
            post_cash = self.get_buying_power()
            current_cash = self.getCashLane(stock)
            additional_cash = float(post_cash)-float(pre_cash)
            cash_lane = float(current_cash)+additional_cash
            qry = Query()
            self.db.update({stock:cash_lane}, qry.type == 'cashlanes')
        except Exception as e:
            print("Error occurred while updating DB with cash", e)

    def cancel_all_ord(self):
        try:
            self.api.cancel_all_orders()
            print("** Canceling all orders **")
        except tradeapi.rest.APIError as e:
            print("Error in cancel_all_ord - ", e)

    def place_order_market(self, symbol, quantity):
        try:
            self.api.submit_order(symbol=symbol,
                                  qty=quantity, side='buy',
                                  time_in_force='day',
                                  type='market')

            print("Placed order ", symbol, " ", quantity)
        except tradeapi.rest.APIError as e:
            print("Error in place_order_market - ", e)

    def close_position(self, symbol):
        try:
            self.api.close_position(symbol=symbol)
            print("Closing position for ", symbol)
        except tradeapi.rest.APIError as e:
            print(e)
            print("Error ocurred while closing position, maybe no open position exist?")

    def get_buying_power(self):
        #BT#
        if self.backtest:
            return self.cash
        ##
        account = self.api.get_account()
        return account.buying_power

    def get_avg_price(self, days=0, symbol=''):

        # TODO Implement market clock
        # Start date is current date and end date is 'days' before start date
        try:
            bars = self.api.get_barset(symbol, timeframe='day', limit=days)
        except tradeapi.rest.APIError as e:
            print("Error in get_avg_price while getting bars- ", e)
        # print(bars)
        closed_end = bars[symbol][-1].c
        closed_start = bars[symbol][0].c
        perc_change = (closed_end-closed_start)/closed_start
        return perc_change

    def getArrayFromBars(self, symbol, days, end):
        try:
            bars = self.api.get_barset(
                symbol, timeframe='day', limit=days, end=end.strftime(BaseAlpha.api_time_format))
        except tradeapi.rest.APIError as e:
            print("Error in get_avg_price while getting bars- ", e)
        ls_o = bars[symbol]
        list_close = [elem.c for elem in ls_o]
        list_open = [elem.o for elem in ls_o]
        list_high = [elem.h for elem in ls_o]
        list_low = [elem.l for elem in ls_o]
        list_date = [elem.t for elem in ls_o]
        list_vol = [elem.v for elem in ls_o]
        np_symbol = np.array(
            [list_close, list_open, list_high, list_low, list_vol])
        idx = pd.DatetimeIndex(list_date)
        np_symbol = np_symbol.transpose()
        df_symbol = pd.DataFrame(np_symbol, index=idx, columns=[
                                 'close', 'open', 'high', 'low', 'volume'])

        #BT#
        if self.backtest:
            self.btPrice = df_symbol['close'][-1]
            self.btPortfolio = self.cash+self.btQty*self.btPrice
            # Check if Stoploss
            if self.btPrice <= self.btStopLossPrice:
                print("STOPLOSS! Selling", self.btQty)
                self.cash = self.cash+self.btPrice*self.btQty
                self.btQty = 0
                self.btStopLossPrice
            print("Price for today", self.btPrice,
                  "Portfolio", self.btPortfolio)
        ##

        return df_symbol

    def isPeak(self, prices):
        dist = len(prices)/2
        ar_prices = np.array(prices)
        ar_peaks, params = find_peaks(ar_prices, distance=dist)
        # print(ar_peaks)
        if (ar_peaks.size > 0) and (ar_peaks[-1] == ar_prices.size-2):
            return True
        else:
            return False

    def isTrough(self, prices):
        dist = len(prices)/2
        ar_prices = np.array(prices)
        ar_troughs, params = find_peaks(-1*ar_prices, distance=dist)
        if (ar_troughs.size > 0) and (ar_troughs[-1] == ar_prices.size-2):
            return True
        else:
            return False

    def isMarketOpen(self):
        clock = self.api.get_clock()
        return clock.is_open, clock.timestamp

    def getCurrentPrice(self, symbol):
        #BT#
        if self.backtest:
            return self.btPrice

        # get latest two minute bars
        bars = self.api.get_barset(symbol, timeframe='minute', limit=2)
        # pick the last one
        latest_bar = bars[symbol][-1]
        # print(bars)
        # print(latest_bar.__getattr__('t'))
        # return the close price of the last bar
        return latest_bar.__getattr__('c')

    def cancelStopLoss(self, symbol):
        #BT#
        if self.backtest:
            self.btStopLossPrice = 0
            return
        ##

        ls_o = self.api.list_orders()
        for o in ls_o:
            # print(o)
            if o.symbol == symbol and o.type == 'stop' and o.side == 'sell':
                self.api.cancel_order(o.id)
                print(
                    "Canceled open order-id:{}, type:{}, side:{}".format(o.id, o.type, o.side))
                status = ""
                count = 0
                while status != "canceled" and count < 5:
                    print("Waiting for StopLoss order to be canceled")
                    time.sleep(1)
                    order = self.getOrder(o.id)
                    status = order.status
                    count = count+1
                if status != "canceled":
                    raise Exception(
                        "Waited for 5 seconds but order did not cancel")

    def getPosition(self, stock):
        return self.api.get_position(stock)

    def calculatePositionSizing(self, cash_lose, buy_price, stoploss_price):
        """ Calculates the size of the position 
            based on the cash willing to loose.
            Pos = cashwilling to lose/ (buy price-stoploss price)
        """
        if buy_price != stoploss_price:
            return int(cash_lose/abs(buy_price-stoploss_price))

    def getRSI(self, df_stock, period):
        df_stock = df_stock.dropna()
        # return the last element of the calculated RSI array
        rsi = talib.RSI(df_stock, timeperiod=period)
        return rsi[-1]

    def setPickle(self, obj, pickle_file):
        with open(pickle_file, 'wb') as f:
            # Pickle the 'data' dictionary using the highest protocol available.
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    def getPickle(self, pickle_file):
        data = {}
        try:
            with open(pickle_file, 'rb') as f:
                # The protocol version used is detected automatically, so we do not
                # have to specify it.
                data = pickle.load(f)
        except FileNotFoundError as e:
            print(e)
        return data

    def getATR(self,df_stock_high,df_stock_low,df_stock_close,period):
        #https://mrjbq7.github.io/ta-lib/func_groups/volatility_indicators.html
        atr = talib.ATR(df_stock_high,df_stock_low,df_stock_close,timeperiod=period)
        return atr[-1]
    
    def getSpeedDF(self,df_stock, period):
        #print(df_stock)
        speed = (df_stock[-1]-df_stock[-int(period)])/int(period)
        return float(speed)
    
    # Compares the given list with the stocks in the portfolio and returns
    # the ones that are NOT in the portfolio
    def getNotOverlappingStocks(self,stock_list):
        list_positions = self.api.list_positions()
        stock_list = list(set(stock_list))
        for position in list_positions:
            if position.symbol in stock_list:
                stock_list.remove(position.symbol)
        return stock_list
