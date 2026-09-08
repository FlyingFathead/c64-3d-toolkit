import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pipeline', ROOT/'perf/pipeline.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)

class PipelineTests(unittest.TestCase):
    def row(self, **changes):
        row=dict(animation='cube',method='yunroll-cart-v9',report='v9',oracle_sha256='abc',
                 observation_seconds=29.86568762382669,display_flips=100,average_fps=100/29.86568762382669,cartridge_bytes=1000,frame_count=24,
                 protocol=dict(mode='normal PLAY ALL ONLY',exhibition=False,loops=3,seconds_setting=10,ticks_per_second=50,pal_clock_hz=985248,vice_defaults=True,seed=1,harness='test'))
        row.update(changes);row['average_fps']=row['display_flips']/row['observation_seconds'];return row
    def state(self, **options):return dict(status='completed',options=options)
    def test_winner_and_tie(self):
        result=pipeline.recommend([self.row(),self.row(report='v8'),self.row(report='v2',display_flips=90)],self.state())
        self.assertEqual(result['winners'][0]['winners'],['v9','v8'])
    def test_incomplete_and_capped_not_ranked(self):
        self.assertNotIn('winners',pipeline.recommend([],dict(status='failed',options={})))
        self.assertNotIn('winners',pipeline.recommend([],self.state(max_fps=10)))
    def test_mismatched_input_rejected(self):
        with self.assertRaises(ValueError):pipeline.recommend([self.row(),self.row(oracle_sha256='other')],self.state())
    def test_mismatched_windows_rejected(self):
        with self.assertRaises(ValueError):pipeline.recommend([self.row(),self.row(observation_seconds=20)],self.state())
    def test_stream_constraint_and_size_limit(self):
        result=pipeline.recommend([self.row(),self.row(method='yunroll',report='resident',display_flips=200),self.row(report='large',cartridge_bytes=3000)],self.state(stream_only=True,max_cart_bytes=2000))
        self.assertEqual(result['winners'][0]['winners'],['v9']);self.assertEqual(len(result['rejected']),2)


class ViewerTests(unittest.TestCase):
    def test_partial_json_is_ignored(self):
        import sys,tempfile
        sys.path.insert(0,str(ROOT/'perf'))
        import watch
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'result.json';p.write_text('{')
            self.assertIsNone(watch.read_json(p))
    def test_terminal_controls_removed(self):
        import sys
        sys.path.insert(0,str(ROOT/'perf'))
        import watch
        self.assertNotIn('\x1b',watch.clean('bad\x1b[2J'))


class WindowRegressionTests(unittest.TestCase):
    def setUp(self):
        import json
        self.reports=json.loads((ROOT/'tests/data/perf-window-boundary.json').read_text())
    def test_real_sphere_windows_do_not_crash(self):
        records=[]
        for name,data in self.reports.items():records+=pipeline.measurement_records(data,{},name)
        span=max(r['observation_seconds'] for r in records)-min(r['observation_seconds'] for r in records)
        self.assertGreater(span,0.01)
        result=pipeline.recommend(records,dict(status='completed',options={}))
        self.assertEqual(result['winners'][0]['winners'],['yunroll'])
    def test_different_protocol_rejected(self):
        records=[]
        for name,data in self.reports.items():records+=pipeline.measurement_records(data,{},name)
        records[0]['protocol']['seed']=2
        with self.assertRaises(ValueError):pipeline.recommend(records,dict(status='completed',options={}))
    def test_corrupt_raw_window_rejected(self):
        data=self.reports['step'];data['samples'][0]['window_cycles']-=5000
        with self.assertRaises(ValueError):pipeline.measurement_records(data,{},'step')
    def test_missing_sample_rejected(self):
        data=self.reports['step'];data['samples'].pop()
        with self.assertRaises(ValueError):pipeline.measurement_records(data,{},'step')
    def test_fps_normalized_not_raw_count(self):
        a=PipelineTests().row(report='a',display_flips=100)
        b=PipelineTests().row(report='b',display_flips=100,observation_seconds=29.855)
        result=pipeline.recommend([a,b],dict(status='completed',options={}))
        self.assertEqual(result['winners'][0]['winners'],['b'])
    def test_viewer_fits_80_columns(self):
        import sys
        sys.path.insert(0,str(ROOT/'perf'));import watch
        rows=[]
        for name,data in self.reports.items():rows+=pipeline.measurement_records(data,{},name)
        ranking=pipeline.recommend(rows,dict(status='completed',options={}))
        data=dict(status='completed',provisional=False,records=rows,leaders=ranking['winners'])
        self.assertTrue(all(len(line)<80 for line in watch.render(data,width=80).splitlines()))
