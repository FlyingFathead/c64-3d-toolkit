from copy import deepcopy
from pathlib import Path
import sys
import unittest
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from benchmark_renderer_history import capacity_reason, selector_coverage, picture_hash, markdown


class HistoryGuards(unittest.TestCase):
    def test_aliases_keep_v2_distinct_and_scene_hardware_explicit(self):
        routes=selector_coverage()
        self.assertEqual(routes['hors-v1']['core'],'yunroll-cart-v10')
        self.assertEqual(routes['hors-v2']['core'],'hors-render-v2')
        self.assertNotEqual(routes['hors-v1'],routes['hors-v2'])
        self.assertEqual(routes['hors-v4-gmod3']['native'],'hors-v4-gmod3')
        self.assertIsNone(routes['hors-v4-gmod3']['core'])
        self.assertEqual(routes['step']['core'],'step')
        self.assertEqual(routes['hors-renderer-v5'],routes['hors-v5-ef'])

    def test_capacity_is_not_a_generic_build_or_pixel_failure(self):
        self.assertIn('frame pointer tables',capacity_reason('error: frame pointer tables reach $1800, limit $1700'))
        for message in ('bitmap mismatch', 'menu title exceeds 40 columns', 'Executable not found', 'assembler syntax error'):
            self.assertIsNone(capacity_reason(message))

    def test_picture_hash_covers_colours_and_order(self):
        blank=dict(records=[],color_spans=[])
        colored=dict(records=[],color_spans=[(0,0,1,0x20)])
        self.assertNotEqual(picture_hash([blank,colored],0),picture_hash([colored,blank],0))
        self.assertNotEqual(picture_hash([blank],0),picture_hash([blank],0x20))

    def test_gmod3_measurements_disable_flash_writeback(self):
        from verify_cart_stream import readonly_cartridge_flags
        with tempfile.TemporaryDirectory() as folder:
            crt=Path(folder)/'test.crt'
            for hardware,expected in ((32,[]),(62,['+gmod3flashwrite'])):
                crt.write_bytes(b'\0'*22+hardware.to_bytes(2,'big'))
                self.assertEqual(readonly_cartridge_flags(crt),expected)

    def test_report_keeps_failed_cases_visible(self):
        rows=[dict(method='step',preference='fps',status='capacity',reason='frame arena exceeded'),
              dict(method='yunroll',preference='fps',status='failed',reason='bitmap mismatch')]
        report=dict(cases=[dict(name='CONTROL',frames=2,pictures_sha256='test',core=dict(protocol='test',rows=rows))])
        result=markdown(report)
        self.assertIn('| step | fps | N/A | N/A | N/A |',result)
        self.assertIn('| yunroll | fps | FAIL | FAIL | FAIL |',result)
        self.assertIn('bitmap mismatch',result)
