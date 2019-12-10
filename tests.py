import alpha as alpha
import unittest



class AlphaTest(unittest.TestCase):
    def test_get_avg_price(self):
        self.assertEqual(alpha.get_avg_price(3,'MSFT'), 0.009605122732123975)

if __name__ == '__main__':
    unittest.main()