import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'perf'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from scene_packing import pack_scene_frames
from c643d.cartridge import easyflash_offset
from c643d.cartscene import pack_scene_frames as sequential

def encode(frame, colors):return frame.block,0

def frame(size, marker=1):return SimpleNamespace(block=bytes([marker,128])+bytes(size-2),records=[])

class PackingTests(unittest.TestCase):
    def test_fragmentation_order_and_directory(self):
        frames=[frame(5000,i+1) for i in range(100)]+[frame(3000,i+101) for i in range(100)]
        with self.assertRaisesRegex(ValueError,'capacity'):sequential(frames,encoder=encode)
        image, entries=pack_scene_frames(frames,encoder=encode,direct_bytes=True)
        self.assertEqual(len(set((d['chip'],d['bank']) for d in entries)),100)
        self.assertEqual(len(image),1048576)
        for i,d in enumerate(entries):
            offset=d['address'] & 8191
            start=easyflash_offset(d['bank'],d['chip'],offset)
            self.assertEqual(image[start:start+d['bytes']],frames[i].block)
            self.assertLessEqual(offset+d['bytes'],8192)
            base=easyflash_offset(1,'romh',0)
            self.assertEqual(image[base+i],d['bank'])
            self.assertEqual(image[base+4*256+i],(d['bytes']>>8)|128)
    def test_aliases_and_second_directory_page(self):
        frames=[frame(32)]*260; aliases=[0]*260
        image,entries=pack_scene_frames(frames,aliases=aliases,encoder=encode)
        self.assertEqual(entries[-1]['address'],entries[0]['address'])
        self.assertEqual(entries[-1]['reference_frame'],0)
        self.assertEqual(image[easyflash_offset(1,'romh',1792)],entries[256]['bank'])
    def test_capacity_and_oversize(self):
        with self.assertRaisesRegex(ValueError,'payload lower bound=123'):
            pack_scene_frames([frame(8192)]*123,encoder=encode)
        with self.assertRaisesRegex(ValueError,'invalid block'):
            pack_scene_frames([frame(8193)],encoder=encode)

class SamplingSweepTests(unittest.TestCase):
    def test_sweep_preserves_duration_and_integer_frames(self):
        from recover_marbles import indices
        for fps in (25,20,19,18,17,16,15):
            samples=indices(1000,25,fps)
            self.assertEqual(len(samples),40*fps)
            self.assertEqual(len(set(samples)),len(samples))
            self.assertTrue(all(isinstance(i,int) and 0<=i<1000 for i in samples))
            self.assertEqual(samples,sorted(samples))
