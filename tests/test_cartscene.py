"""Boundary coverage for the opt-in long-scene cartridge format."""
import unittest
from tools.c643d.pipeline import FrameBuild
from tools.c643d.cartscene import pack_scene_frames,validate_hud
from tools.c643d.cartstream import frame_block,pack_frames
from tools.c643d.cartridge import easyflash_offset
from tools.c643d.font import glyph

class SceneStreamTests(unittest.TestCase):
    def frame(self,n=1):
        return FrameBuild([(0,0,2,0,0)]*n,[(0,0,1)],2*n,2,[],[(0,0,1,0x30)])

    def test_directory_pages_and_high_frame_indices_roundtrip(self):
        frames=[self.frame(1+i%4) for i in range(2048)]
        image,entries=pack_scene_frames(frames)
        for i in (0,254,255,256,511,512,1023,1024,1792,2047):
            d=entries[i];page=i//256;idx=i%256
            base=easyflash_offset(1+page//4,'romh',page%4*1792)
            values=[image[base+field*256+idx] for field in range(7)]
            self.assertEqual(values,[d['bank'],d['address']&255,d['address']>>8,d['bytes']&255,d['bytes']>>8,d['metadata_bytes']&255,d['metadata_bytes']>>8])
            off=easyflash_offset(d['bank'],d['chip'],d['address']-(0x8000 if d['chip']=='roml' else 0xa000))
            self.assertEqual(bytes(image[off:off+d['bytes']]),frame_block(frames[i])[0])
        with self.assertRaisesRegex(ValueError,'1..2048'):pack_scene_frames(frames+[frames[0]])
        with self.assertRaisesRegex(ValueError,'1..255'):pack_frames(frames[:256])

    def test_dual_chip_boundary_capacity_and_no_frame_crosses_bank(self):
        frames=[self.frame(900)]*122
        image,entries=pack_scene_frames(frames)
        self.assertEqual((entries[60]['chip'],entries[60]['bank']),('roml',63))
        self.assertEqual((entries[61]['chip'],entries[61]['bank']),('romh',3))
        self.assertEqual((entries[-1]['chip'],entries[-1]['bank']),('romh',63))
        for f,d in zip(frames,entries):
            base=0x8000 if d['chip']=='roml' else 0xa000
            self.assertLessEqual(d['address']+d['bytes'],base+8192)
            off=easyflash_offset(d['bank'],d['chip'],d['address']-base)
            self.assertEqual(bytes(image[off:off+d['bytes']]),frame_block(f)[0])
        with self.assertRaisesRegex(ValueError,'capacity'):pack_scene_frames(frames+[frames[0]])

    def test_hud_apostrophe_and_reject_silent_truncation(self):
        self.assertEqual(validate_hud("don't lose your marbles"),"DON'T LOSE YOUR MARBLES")
        self.assertNotEqual(glyph("'"),glyph(' '))
        with self.assertRaises(ValueError):validate_hud('A'*32)
        with self.assertRaises(ValueError):validate_hud('£')

if __name__=='__main__':unittest.main()
