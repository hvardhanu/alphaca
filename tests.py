import alpaca_trade_api as tradeapi
import BaseAlpha
import unittest
import datetime
from unittest.mock import Mock,patch

class AlphaTest(unittest.TestCase):
    def setUp(self): 
        pass
        
    def test_closePositionStock(self):
        with patch('BaseAlpha.tradeapi') as mock:
            api = mock.return_value
            api.close_position.return_value = {}
            base = BaseAlpha.BaseAlpha()
            base.api = api
            base.closePositionStock('MSFT')
            self.assertEqual(api.close_position.call_count,1)
    
    def test_placeBuyWithStop(self):
        with patch('BaseAlpha.tradeapi') as mock:
            #Set up mock API
            api = mock.return_value
            base = BaseAlpha.BaseAlpha()
            base.api = api

            #Set up some mock API Responses
            mockbuyorder = Mock()
            mockbuyorder.status = 'filled'
            mockbuyorder.id = 1234
            mockbuyorder.filled_qty = 2
            mockbuyorder.filled_avg_price = 10
            api.submit_order.return_value = mockbuyorder

            mockstatusorder = Mock()
            mockstatusorder.status = 'filled'
            mockstatusorder.id = 1234
            mockstatusorder.filled_qty = 2
            mockstatusorder.filled_avg_price = 10
            api.get_order.return_value = mockstatusorder
            
            #Test
            self.assertEqual(base.placeBuyWithStop('MSFT',1,1),True)
            self.assertEqual(api.submit_order.call_count,2)
            api.submit_order.reset_mock()

            mockstatusorder.status = 'pending'
            self.assertEqual(base.placeBuyWithStop('MSFT',1,1),False)
            self.assertEqual(api.submit_order.call_count,1)
            api.submit_order.reset_mock()

            #Make the API submit order function raise an exception
            api.submit_order.side_effect = Exception("BOOM!")
            self.assertEqual(base.placeBuyWithStop('MSFT',1,1),False)
            self.assertEqual(api.submit_order.call_count,1)
        
    def test_cancelStopLoss(self):
        with patch('BaseAlpha.tradeapi') as mock:
            #Set up mock API
            api = mock.return_value
            base = BaseAlpha.BaseAlpha()
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

    def test_getPosition(self):
        with patch('BaseAlpha.tradeapi') as mock:
            #Set up mock API
            api = mock.return_value
            base = BaseAlpha.BaseAlpha()
            base.api = api
            
            mockPosition = Mock()
            mockPosition.qty=1

            base.api.get_position.return_value=mockPosition
            position = base.getPosition('MSFT')
            self.assertGreaterEqual(position.qty,0)

    def test_getArrayFromBars(self):
        days = 2
        base = BaseAlpha.BaseAlpha()
        df=base.getArrayFromBars('MSFT',days,datetime.datetime.now())
        print(df)
        self.assertEqual(len(df),days)
        self.assertEqual(len(df.columns),5)
        self.assertIn('close',df.columns)
        self.assertIn('open',df.columns)
        self.assertIn('volume',df.columns)
        self.assertIn('high',df.columns)
        self.assertIn('low',df.columns)


if __name__ == '__main__':
    unittest.main()