"""V8 wire decoding against original pixels and unchanged V7 fallback bytes."""
import random
import unittest
from pathlib import Path

from tools.c643d.bytespan import frame_block, spans_for_bitmap, configure_source
from tools.c643d.cartstream import frame_block as v7_block
from tools.c643d.pipeline import FrameBuild, encode_run, oriented_dda
from tools.c643d.optimize import picture_bytes
from tools.c643d.clearplan import selective_clear
from tools.c643d.cli import make_parser
from tools.c643d.toolchain import load_toolchain_settings


def fixture(offsets):
    records = []
    cells = sorted({o // 8 for o in offsets})
    for offset in offsets:
        row, col = divmod(offset, 320)
        x, y = (col // 8) * 8, row * 8 + col % 8
        dda = oriented_dda(x, y, x+1, y)
        records.append(encode_run(dda, 0, 1))
    return FrameBuild(records, [(c*8 & 255, c*8 >> 8, 1) for c in cells],
                      len(records)*2, len(records)*2, [],
                      [(c & 255, c >> 8, 1, 112) for c in cells])


class V8Tests(unittest.TestCase):
    def test_previous_renderers_and_binaries_are_byte_identical(self):
        import hashlib
        import json
        root = Path(__file__).resolve().parents[1]
        frozen = json.loads((root/'tests/data/preserved-v0.6.7.json').read_text())
        for name, expected in frozen['files'].items():
            if name.startswith('../'): continue  # Checked separately when the external archive is available.
            self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(), expected, name)

    def test_external_historical_binaries(self):
        import hashlib, json
        root=Path(__file__).resolve().parents[1]
        frozen=json.loads((root/'tests/data/preserved-v0.6.7.json').read_text())
        external={k:v for k,v in frozen['files'].items() if k.startswith('../')}
        if not (root.parent/'c64-3d-toolkit-history').exists():
            self.skipTest('Optional historical archive is outside the checkout and not installed')
        missing = []
        for name, expected in external.items():
            if not (root/name).is_file():
                missing.append(name)
                continue
            self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),expected,name)
        if missing:
            self.skipTest(f'Optional historical archive is incomplete: {len(missing)} reference files absent')

    def assert_wire_picture(self, frame):
        original, meta = v7_block(frame)
        encoded, actual_meta = frame_block(frame)
        self.assertEqual(meta, actual_meta)
        self.assertEqual(encoded[:meta], original[:meta])
        self.assertLessEqual(len(encoded), len(original))
        count = int.from_bytes(encoded[meta:meta+2], 'little')
        if not count & 0x8000:
            self.assertEqual(encoded, original)
            return
        bitmap = bytearray(7680)
        cursor = meta+2
        for _ in range(count & 0x7fff):
            offset = int.from_bytes(encoded[cursor:cursor+2], 'little')
            length = encoded[cursor+2]
            self.assertGreater(length, 0)
            self.assertLessEqual(offset+length, 7680)
            bitmap[offset:offset+length] = encoded[cursor+3:cursor+3+length]
            cursor += 3+length
        self.assertEqual(cursor, len(encoded))
        self.assertEqual(bitmap, picture_bytes(frame)[:7680])

    def test_span_lengths_gaps_and_page_boundaries(self):
        for length in (1, 2, 3, 7, 8, 127, 128, 254, 255, 256, 511):
            for start in (0, 249, 256, 7000):
                self.assert_wire_picture(selective_clear(fixture(range(start, start+length)))[0])

    def test_random_sparse_pictures(self):
        rng = random.Random(8)
        for _ in range(30):
            offsets = sorted(rng.sample(range(2000), 100))
            self.assert_wire_picture(fixture(offsets))

    def test_vector_fallback_and_empty_picture(self):
        dda = oriented_dda(0, 0, 126, 0)
        frame = fixture([])
        frame.records = [encode_run(dda, 0, 126)]
        self.assertEqual(frame_block(frame), v7_block(frame))
        self.assertEqual(frame_block(fixture([])), v7_block(fixture([])))

    def test_extent_and_compile_time_dispatch(self):
        bitmap = bytearray(7680)
        bitmap[0] = bitmap[-1] = 255
        self.assertEqual(spans_for_bitmap(bitmap), [(0, b'\xff'), (7679, b'\xff')])
        with self.assertRaises(ValueError):
            spans_for_bitmap(bitmap[:-1])
        self.assertEqual(configure_source('V8_BYTE_SPANS = 0', []), 'V8_BYTE_SPANS = 0')
        self.assertEqual(configure_source('V8_BYTE_SPANS = 0', [{'encoding': 'byte-spans'}]), 'V8_BYTE_SPANS = 1')

    def test_cli_keeps_old_defaults_and_accepts_v8(self):
        parser = make_parser(load_toolchain_settings(Path('/missing/c643d.ini')))
        self.assertEqual(parser.parse_args(['build']).renderer, 'hors-render-v1')
        self.assertEqual(parser.parse_args(['cart-demos']).stream_renderer, 'hors-render-v1')
        for renderer in ('yunroll-cart-v8', 'yunroll-cart-v8-scene'):
            self.assertEqual(parser.parse_args(['build', '--renderer', renderer]).renderer, renderer)


class V8PlayAllTests(unittest.TestCase):
    def test_exhibition_durations_are_v8_only_and_follow_names(self):
        from tools.c643d.cartuniform import play_all_durations
        entries=[{'name':n} for n in ('HORSE HEAD HIFI','CUBE','SUNFLOWER TORUS HIFI','HORSE HEAD')]
        self.assertEqual(play_all_durations(entries,10,'yunroll-cart-v8'),[15,10,15,10])
        self.assertEqual(play_all_durations(entries,10,'yunroll-cart-v7'),[10]*4)
        self.assertEqual(play_all_durations(entries,20,'yunroll-cart-v8'),[20]*4)
