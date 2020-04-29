import alpaca_trade_api as tradeapi
import BaseAlpha
import unittest
import datetime
from unittest.mock import Mock,patch
from tinydb import TinyDB, Query

# to run 
# python *.py
# python -m unittest test_module.TestClass.test_method

class AlphaTest(unittest.TestCase):
    def setUp(self): 
         self.base = BaseAlpha.BaseAlpha('unitest')
         self.db = TinyDB("unitest.json")
         self.db.insert({"type":"cashlanes","MSFT":100,"CORGI":1000,"HUSKY":6000})
         self.db.insert({"type":"periods","MSFT":10,"CORGI":5,"HUSKY":6})
         self.db.insert({"type":"stoploss","MSFT":10,"CORGI":20,"HUSKY":0.56})
         

    def tearDown(self):
         self.db.purge()

    def test_getStocks(self):
        stocks = self.base.getStocks()
        self.assertTrue("MSFT" in stocks)
        self.assertTrue("CORGI" in stocks)
        self.assertTrue("HUSKY" in stocks)
        self.assertFalse("type" in stocks)
        self.assertFalse("XC" in stocks)
    
    def test_getPeriod(self):
        self.assertEqual(self.base.getPeriod('MSFT'),10)
        self.assertEqual(self.base.getPeriod('CORGI'),5)
        self.assertEqual(self.base.getPeriod('HUSKY'),6)
        self.assertEqual(self.base.getPeriod('XC'),0)
    
    def test_getStoploss(self):
        self.assertEqual(self.base.getStoploss('MSFT'),10)
        self.assertEqual(self.base.getStoploss('CORGI'),20)
        self.assertEqual(self.base.getStoploss('HUSKY'),0.56)
        self.assertEqual(self.base.getStoploss('XC'),0)
    
    def test_getCashLane(self):
        self.assertEqual(self.base.getCashLane('MSFT'),100)
        self.assertEqual(self.base.getCashLane('CORGI'),1000)
        self.assertEqual(self.base.getCashLane('HUSKY'),6000)
        self.assertEqual(self.base.getCashLane('XC'),0)

    def test_closePositionStock(self):
        with patch('BaseAlpha.tradeapi') as mock:
            api = mock.return_value
            api.close_position.return_value = {}
            mockAccount1 = Mock()
            mockAccount1.buying_power = 100
            mockAccount2 = Mock()
            mockAccount2.buying_power = 110
            api.get_account.side_effect = [mockAccount1,mockAccount2]
            base = BaseAlpha.BaseAlpha('unitest')
            base.api = api
            base.closePositionStock('MSFT')
            self.assertEqual(api.close_position.call_count,1)
    
    def test_placeBuyWithStop(self):
        with patch('BaseAlpha.tradeapi') as mock:
            #Set up mock API
            api = mock.return_value
            base = BaseAlpha.BaseAlpha('unitest')
            base.api = api

            #Set up some mock API Responses
            mockbuyorder = Mock()
            mockbuyorder.status = 'filled'
            mockbuyorder.symbol = 'MSFT'
            mockbuyorder.id = 1234
            mockbuyorder.submitted_at='12-12-2017'
            mockbuyorder.filled_at = ''
            mockbuyorder.qty = 2
            mockbuyorder.type = 'market'
            mockbuyorder.side = 'buy'
            mockbuyorder.filled_qty = 2
            mockbuyorder.filled_avg_price = 10
            api.submit_order.return_value = mockbuyorder

            mockstatusorder = Mock()
            mockstatusorder.status = 'filled'
            mockstatusorder.symbol = 'MSFT'
            mockstatusorder.filled_at=''
            mockstatusorder.submitted_at='12-12-2017'
            mockstatusorder.type = 'market'
            mockstatusorder.side = 'buy'
            mockstatusorder.id = 1234
            mockstatusorder.qty = 2
            mockstatusorder.filled_qty = 2
            mockstatusorder.filled_avg_price = 10
            api.get_order.return_value = mockstatusorder
            
            #Test the goodie scenario, buy goes through -> stoploss goes through
            # Expected - return True
            self.assertEqual(base.placeBuyWithStop('MSFT',1,1),1234)
            self.assertEqual(api.submit_order.call_count,2)
            self.assertEqual(api.cancel_order.call_count,0)
            self.assertEqual(api.close_position.call_count,0)
            api.submit_order.reset_mock()
            api.cancel_order.reset_mock()
            api.close_position.reset_mock()

            #Buy takes > 5 sec to execute
            # Expected - cancel buy order and return False
            mockstatusorder.status = 'pending'
            self.assertEqual(base.placeBuyWithStop('MSFT',1,1),False)
            self.assertEqual(api.submit_order.call_count,1)
            self.assertEqual(api.cancel_order.call_count,1)
            self.assertEqual(api.close_position.call_count,0)
            api.submit_order.reset_mock()
            api.cancel_order.reset_mock()
            api.close_position.reset_mock()
            
            # Buy throws an exception an exception
            # Expected - As we failed to place buy order, just return false and do nothing else
            api.submit_order.side_effect = Exception("BOOM!")
            self.assertEqual(base.placeBuyWithStop('MSFT',1,1),False)
            self.assertEqual(api.submit_order.call_count,1)
            self.assertEqual(api.cancel_order.call_count,0)
            self.assertEqual(api.close_position.call_count,0)
            api.submit_order.reset_mock()
            api.cancel_order.reset_mock()
            api.close_position.reset_mock()
            api.submit_order.side_effect=None

            # Buy order goes through, but the stoploss order fails
            # Expected - cancel_order should be called to cancel the buy order
            mockstatusorder.status = 'filled'
            # The submit_order first returns a mock object then throws exception
            api.submit_order.side_effect = [mockbuyorder,Exception("BOOM! Stoploss order failed")]
            self.assertEqual(base.placeBuyWithStop('MSFT',1,1),False)
            self.assertEqual(api.submit_order.call_count,2)
            self.assertEqual(api.cancel_order.call_count,1)
            self.assertEqual(api.close_position.call_count,0)
            api.submit_order.reset_mock()
            api.cancel_order.reset_mock()
            api.close_position.reset_mock()

            #Buy order goes through -> stoploss order fails -> cancel buy order fails
            #Expected - as we failed to put stoploss & failed to cancel buy order, we should close any open positions
            api.submit_order.side_effect = [mockbuyorder,Exception("BOOM! Stoploss order failed")]
            api.cancel_order.side_effect = Exception("BOOM! Exception while canceling order")
            self.assertEqual(base.placeBuyWithStop('MSFT',1,1),False)
            self.assertEqual(api.submit_order.call_count,2)
            self.assertEqual(api.cancel_order.call_count,1)
            self.assertEqual(api.close_position.call_count,1)
            api.submit_order.reset_mock()
            api.cancel_order.reset_mock()
            api.close_position.reset_mock()

            
        
    def test_cancelStopLoss(self):
        with patch('BaseAlpha.tradeapi') as mock:
            #Set up mock API
            api = mock.return_value
            base = BaseAlpha.BaseAlpha('unitest')
            base.api = api

            #Set up some mock API Responses
            ls_ord=[]
            mockorder1 = Mock()
            mockorder1.status = 'new'
            mockorder1.side = 'sell'
            mockorder1.symbol = 'MSFT'
            mockorder1.type = 'stop'
            ls_ord.append(mockorder1)

            mockorder2 = Mock()
            mockorder2.status = 'filled'
            mockorder2.id = 1234
            mockorder2.filled_qty = 2
            mockorder2.filled_avg_price = 10
            ls_ord.append(mockorder2)
            
            mockcanceledOrder = Mock()
            mockcanceledOrder.status = "canceled"
            api.get_order.return_value=mockcanceledOrder

            api.list_orders.return_value = ls_ord
            base.cancelStopLoss('MSFT')
            self.assertEqual(api.cancel_order.call_count,1)
            self.assertEqual(api.get_order.call_count,1)

    def test_getPosition(self):
        with patch('BaseAlpha.tradeapi') as mock:
            #Set up mock API
            api = mock.return_value
            base = BaseAlpha.BaseAlpha('unitest')
            base.api = api
            
            mockPosition = Mock()
            mockPosition.qty=1

            base.api.get_position.return_value=mockPosition
            position = base.getPosition('MSFT')
            self.assertGreaterEqual(position.qty,0)

    def test_getArrayFromBars(self):
        days = 2
        df=self.base.getArrayFromBars('MSFT',days,datetime.datetime.now())
        print(df)
        self.assertEqual(len(df),days)
        self.assertEqual(len(df.columns),5)
        self.assertIn('close',df.columns)
        self.assertIn('open',df.columns)
        self.assertIn('volume',df.columns)
        self.assertIn('high',df.columns)
        self.assertIn('low',df.columns)
    
    def test_calculatePositionSizing(self):
        self.assertEqual(self.base.calculatePositionSizing(2000,130,120),200)
        self.assertEqual(self.base.calculatePositionSizing(2000,120,130),200)
        self.assertEqual(self.base.calculatePositionSizing(100,121,130),11)
        self.assertEqual(self.base.calculatePositionSizing(100,4.1,4.8),142)

    def test_getNotOverlappingStocks(self):
        with patch('BaseAlpha.tradeapi') as mock:
            #Set up mock API
            base = BaseAlpha.BaseAlpha('unitest')

            mockPosition1 = Mock()
            mockPosition1.symbol='MSFT'
            mockPosition2 = Mock()
            mockPosition2.symbol='F'
            mockPosition3 = Mock()
            mockPosition3.symbol='GM'

            base.api.list_positions.return_value=[mockPosition1,mockPosition3,mockPosition2]
            #mock.list_positions.return_value='SAS'

            self.assertEqual(base.getNotOverlappingStocks(['MSFT','GM']),[])
            self.assertEqual(base.getNotOverlappingStocks(['MSFT','SBX']),['SBX'])
            self.assertEqual(sorted(base.getNotOverlappingStocks(['C','SBX'])),sorted(['C','SBX']))
            self.assertEqual(sorted(base.getNotOverlappingStocks(['C','SBX','DF'])),sorted(['C','SBX','DF']))
            self.assertEqual(base.getNotOverlappingStocks([]),[])
            self.assertEqual(base.api.list_positions.call_count,5)


if __name__ == '__main__':
    unittest.main()