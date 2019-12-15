import alpha as alpha
import unittest



class AlphaTest(unittest.TestCase):
    def setUp(self): 
        pass

    def test_get_avg_price(self):
        self.assertEqual(alpha.get_avg_price(4,'MSFT'), -0.00382207578253715)
    
    def test_bought_strategy(self):
        sample_return = -0.7
        self.assertEqual(alpha.strategy('MSFT',sample_return,True),"BOUGHT")
    
    def test_sold_strategy(self):
        sample_return = 0.7
        self.assertEqual(alpha.strategy('MSFT',sample_return, True),"SOLD")

    def tearDown(self):
        alpha.cancelAllOrders()


if __name__ == '__main__':
    unittest.main()