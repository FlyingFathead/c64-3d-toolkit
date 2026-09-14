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

    def test_models_rank_only_average(self):
        source=['| Model | Method | High FPS | Average FPS | Low FPS |','| --- | --- | ---: | ---: | ---: |',
                '| A | v1 | 50 | 20 | 10 |','| B | v1 | 80 | 40 | 30 |',
                '| A | v2 | 40 | 21 | 12 |','| B | v2 | 80 | 35 | 31 |']
        text='\n'.join(highlight_fps(source))
        self.assertIn('| A | v1 | 50 | 20 | 10 |',text)
        self.assertIn('| A | v2 | 40 | **21** | 12 |',text)
        self.assertIn('| B | v1 | 80 | **40** | 30 |',text)
        self.assertIn('| B | v2 | 80 | 35 | 31 |',text)

    def test_sande_models_have_separate_idempotent_tables(self):
        source=['| Model | Method | Average FPS |','| --- | --- | ---: |',
            "| Sande's Pretzel | V2 | 20 |","| Sande's TAC-2 | V2 | 30 |",
            "| Sande's Pretzel | V3 | 25 |","| Sande's TAC-2 | V3 | 32 |"]
        result=highlight_fps(source)
        self.assertIn("#### Sande's Pretzel",result)
        self.assertIn("#### Sande's TAC-2",result)
        self.assertEqual(highlight_fps(result),result)

    def test_two_average_columns_compare_within_each_row(self):
        result=highlight_fps(['| Scene | EasyFlash average FPS | GMod3 average FPS |',
            '| --- | ---: | ---: |','| A | 10.0 | 10.5 |','| B | 11 | 11 |'])
        self.assertEqual(result[2],'| A | 10.0 | **10.5** |')
        self.assertEqual(result[3],'| B | **11 (tie)** | **11 (tie)** |')
