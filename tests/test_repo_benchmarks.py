from dataclasses import asdict
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from benchmark_repo_examples import geometry_clears
from c643d.pipeline import FrameBuild, decode_record_points
from verify_cart_stream import expected_frame


class PublishedOracleNormalization(unittest.TestCase):
    def test_byte_clear_oracle_becomes_safe_for_original_cores(self):
        # Three-pixel horizontal record at (100, 40), and a V7 byte clear.
        record=(160,6,3,4,0)
        original=FrameBuild([record],[(160,134,1)],3,3,[],[(212,0,1,32)])
        normalized=geometry_clears(original)
        self.assertEqual(expected_frame(asdict(original),16),expected_frame(asdict(normalized),16))
        touched={(y//8)*320+(x//8)*8 for x,y in decode_record_points(record)}
        cleared={lo+(hi<<8)+j*8 for lo,hi,n in normalized.clear_spans for j in range(n)}
        self.assertEqual(touched,cleared)
        self.assertTrue(all(hi<128 and n<=32 for lo,hi,n in normalized.clear_spans))
        self.assertEqual(original.clear_spans,[(160,134,1)])

if __name__=='__main__':unittest.main()
