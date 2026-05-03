import unittest
from ssqcore.strategy import random_strategy

class TestStrategy(unittest.TestCase):
    def test_random_strategy(self):
        red, blue = random_strategy()
        self.assertEqual(len(red), 6)
        self.assertTrue(all(1 <= n <= 33 for n in red))
        self.assertTrue(1 <= blue <= 16)
        self.assertEqual(len(set(red)), 6)

if __name__ == '__main__':
    unittest.main()
