import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'perf'))
from recover_marbles import timing_check

class RealtimeSelectionTests(unittest.TestCase):
    def report(self,seconds,cycles):
        return dict(measured_seconds=seconds,samples=[dict(render_cycles=n) for n in cycles])
    def test_rejects_observed_slow_motion(self):
        self.assertFalse(timing_check(self.report(64.3066,[78291,286921]),20)['passed'])
    def test_rejects_local_stall_even_with_good_average(self):
        self.assertFalse(timing_check(self.report(40,[10000,100000]),20)['passed'])
    def test_accepts_normal_timing(self):
        self.assertTrue(timing_check(self.report(40.05,[10000,35000]),20)['passed'])
    def test_rejects_fast_forward(self):
        self.assertFalse(timing_check(self.report(30,[10000]),20)['passed'])
