import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'perf'))
import byte_candidates as experiment

class CandidatePolicyTests(unittest.TestCase):
    def source(self):return "def choose(data, original, meta=0):\n    "+experiment.ORIGINAL+'\n'
    def choose(self,policy,a,b):
        scope={};exec(experiment.patch_encoder(self.source(),policy),scope)
        return scope['choose'](b'A'*a,b'B'*b)[0]
    def test_baseline_preserved(self):
        s=self.source();self.assertEqual(experiment.patch_encoder(s,'baseline'),s)
        self.assertEqual(self.choose('baseline',100,100),b'B'*100)
    def test_125_boundary(self):
        self.assertEqual(self.choose('bytes125',125,100),b'A'*125)
        self.assertEqual(self.choose('bytes125',126,100),b'B'*100)
    def test_150_boundary(self):
        self.assertEqual(self.choose('bytes150',150,100),b'A'*150)
        self.assertEqual(self.choose('bytes150',151,100),b'B'*100)
    def test_force_and_bank_bound(self):
        self.assertEqual(self.choose('force-bytes',200,100),b'A'*200)
        with self.assertRaises(ValueError):self.choose('force-bytes',8193,100)
    def test_adapter_rejects_unknown_source(self):
        with self.assertRaises(ValueError):experiment.patch_encoder('wrong','force-bytes')
