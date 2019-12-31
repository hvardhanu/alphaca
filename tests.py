import alpaca_trade_api as tradeapi
import BaseAlpha
import unittest
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


if __name__ == '__main__':
    unittest.main()