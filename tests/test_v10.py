import unittest
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from c643d.blender import output_frame_plan
from c643d import bytespan_v10, cli
from c643d.toolchain import load_toolchain_settings

class V10Tests(unittest.TestCase):
    def test_source_timing(self):
        _,samples=output_frame_plan(1,1000,25,25,1)
        self.assertEqual(len(samples),1000)
        self.assertEqual(samples[0],1)
        self.assertEqual(samples[-1],1000)
        _,samples=output_frame_plan(1,1000,25,20,1)
        self.assertEqual(len(samples),800)
        self.assertEqual(samples[1],2)
        self.assertTrue(all(isinstance(f,int) for f in samples))
        _,repeated=output_frame_plan(1,1000,25,50,1)
        self.assertEqual(len(repeated),2000)
        self.assertEqual(len(set(repeated)),1000)
        self.assertEqual(len(samples)/20,40)
    def test_old_renderer_rejects_rate_override(self):
        p=cli.make_parser(load_toolchain_settings(Path('/missing.ini')))
        a=p.parse_args(['build','--renderer','yunroll-cart-v9-scene','--blend','x.blend','--blender-output-fps','25'])
        with self.assertRaisesRegex(ValueError,'requires --blend with V10'):cli.cmd_build(a)
    def test_byte_policy_falls_back_at_bank_limit(self):
        with patch('c643d.cartstream.frame_block',return_value=(b'\0\0',0)),patch.object(bytespan_v10,'picture_bytes',return_value=bytes(7680)),patch.object(bytespan_v10,'spans_for_bitmap',return_value=[(i*255,bytes(255)) for i in range(33)]):
            self.assertEqual(bytespan_v10.frame_block(None),(b'\0\0',0))
    def test_byte_policy_can_spend_more_rom(self):
        with patch('c643d.cartstream.frame_block',return_value=(b'\0\0',0)),patch.object(bytespan_v10,'picture_bytes',return_value=bytes(7680)),patch.object(bytespan_v10,'spans_for_bitmap',return_value=[(0,b'\xff')]):
            data,meta=bytespan_v10.frame_block(None)
            self.assertGreater(len(data),2)
            self.assertEqual(data[1]&128,128)
