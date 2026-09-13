import unittest
from tools.performance_tables import highlight_fps

class PerformanceTables(unittest.TestCase):
    def test_row_comparison_marks_both_ties_and_leaves_storage(self):
        source=['| Scene | v1 FPS | v2 FPS | ROM bytes |','| --- | ---: | ---: | ---: |',
                '| one | 12.10 | 12.10 | 9000 |','| two | 13.00 | 18.00 | 3000 |']
        result=highlight_fps(source)
        self.assertEqual(result[2],'| one | **12.10 (tie)** | **12.10 (tie)** | 9000 |')
        self.assertEqual(result[3],'| two | 13.00 | **18.00** | 3000 |')
        self.assertEqual(highlight_fps(result),result)

    def test_models_and_extrema_are_ranked_separately(self):
        source=['| Model | Method | High FPS | Average FPS | Low FPS |','| --- | --- | ---: | ---: | ---: |',
                '| A | v1 | 50 | 20 | 10 |','| B | v1 | 80 | 40 | 30 |',
                '| A | v2 | 40 | 21 | 12 |','| B | v2 | 80 | 35 | 31 |']
        text='\n'.join(highlight_fps(source))
        self.assertIn('| A | v1 | **50** | 20 | 10 |',text)
        self.assertIn('| A | v2 | 40 | **21** | **12** |',text)
        self.assertIn('| B | v1 | **80 (tie)** | **40** | 30 |',text)
        self.assertIn('| B | v2 | **80 (tie)** | 35 | **31** |',text)
