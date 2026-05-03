import unittest
from ssqcore.analysis import frequency_analysis, missing_analysis

class TestAnalysis(unittest.TestCase):
    def setUp(self):
        self.records = [
            {'red': [1,2,3,4,5,6], 'blue': 7},
            {'red': [2,3,4,5,6,7], 'blue': 8},
            {'red': [3,4,5,6,7,8], 'blue': 9},
        ]

    def test_frequency_analysis(self):
        red_counter, blue_counter = frequency_analysis(self.records)
        self.assertEqual(red_counter[3], 3)
        self.assertEqual(blue_counter[7], 1)
        self.assertEqual(blue_counter[8], 1)
        self.assertEqual(blue_counter[9], 1)

    def test_missing_analysis(self):
        red_missing, blue_missing = missing_analysis(self.records)
        self.assertEqual(red_missing[1], 2)
        self.assertEqual(blue_missing[7], 2)

if __name__ == '__main__':
    unittest.main()
