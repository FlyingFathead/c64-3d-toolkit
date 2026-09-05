"""Format/memory-boundary checks; pixel correctness is verified in real VICE."""
import unittest
from tools.c643d.pipeline import FrameBuild
from tools.c643d.cartstream import frame_block,pack_frames
from tools.c643d.cartridge import easyflash_offset

class StreamFormatTests(unittest.TestCase):
    def frame(self,records=1):
        return FrameBuild([(0,0,2,0,0)]*records,[(0,0,1)],2*records,2,[],[(0,0,1,0x40)])
    def test_word_count_and_metadata(self):
        f=self.frame(351);blob,n=frame_block(f)
        self.assertEqual(n,9)
        self.assertEqual(blob[:n],bytes([1,0,0,1,1,0,0,1,0x40]))
        self.assertEqual(int.from_bytes(blob[n:n+2],'little'),351)
        self.assertEqual(len(blob),n+2+351*5)
    def test_bank_packing_roundtrip_and_boundary(self):
        frames=[self.frame(900) for _ in range(61)]
        image,directory=pack_frames(frames)
        self.assertEqual([d['bank'] for d in directory],list(range(3,64)))
        for f,d in zip(frames,directory):
            a=easyflash_offset(d['bank'],'roml',d['address']-0x8000)
            self.assertEqual(bytes(image[a:a+d['bytes']]),frame_block(f)[0])
            self.assertLessEqual(d['address']+d['bytes'],0xa000)
        with self.assertRaisesRegex(ValueError,'capacity'):pack_frames(frames+[self.frame(900)])
    def test_frame_and_metadata_capacity(self):
        with self.assertRaisesRegex(ValueError,'staging'):frame_block(self.frame(1700))
        f=self.frame();f.clear_spans=[(0,0,1)]*200;f.color_spans=[(0,0,1,0x40)]*200
        with self.assertRaisesRegex(ValueError,'cache'):frame_block(f)
    def test_directory_limit_and_legacy_compatible_monochrome(self):
        with self.assertRaisesRegex(ValueError,'1..255'):pack_frames([self.frame()]*256)
        blob,n=frame_block(self.frame(1),False)
        self.assertEqual(n,4)
        self.assertEqual(blob[:n],bytes([1,0,0,1]))
        self.assertEqual(int.from_bytes(blob[n:n+2],'little'),1)
    def test_empty_frame_keeps_zero_word(self):
        f=FrameBuild([],[],0,0,[])
        self.assertEqual(frame_block(f,False),(bytes([0,0,0]),1))

if __name__=='__main__':unittest.main()
