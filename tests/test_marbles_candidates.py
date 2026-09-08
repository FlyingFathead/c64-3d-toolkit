import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'perf'))
from marbles_candidates import metrics

class MarblesMetricsTests(unittest.TestCase):
    def sample(self):
        return dict(sha256='same',clock_hz=985248,render_budget_cycles=150,frames=2,
                    samples=[dict(frame=0,render_cycles=100,total_cycles=200),
                             dict(frame=1,render_cycles=200,total_cycles=400)])
    def test_weighted_rate_and_budget(self):
        p=self.sample();r=metrics([p,copy.deepcopy(p)])
        self.assertEqual(r['mean_render_cycles'],150)
        self.assertEqual(r['render_over_budget'],2)
        self.assertEqual(r['profile_interval_fps_avg'],985248/300)
    def test_reject_different_cartridge(self):
        a=self.sample();b=self.sample();b['sha256']='different'
        with self.assertRaises(ValueError):metrics([a,b])
    def test_reject_missing_source_frame(self):
        a=self.sample();a['samples'][1]['frame']=0
        with self.assertRaises(ValueError):metrics([a])
