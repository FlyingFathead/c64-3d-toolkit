import gzip
import json
from pathlib import Path
import unittest

from tools.c643d import hors_v3, hors_v5, hors_v2_stable
from tools.c643d.pipeline import FrameBuild
from tools.c643d.optimize import picture_bytes
from tools.c643d.renderer_names import canonical_selector, DEFAULT_RENDERER
from tools.c643d.cli import make_parser
from tools.c643d.toolchain import load_toolchain_settings

ROOT = Path(__file__).resolve().parents[1]


class HorsV5Tests(unittest.TestCase):
    def test_opt_in_and_preserved_default(self):
        self.assertEqual(DEFAULT_RENDERER, 'hors-v4')
        parser = make_parser(load_toolchain_settings(None))
        for name in ('hors-v5', 'hors-v5-ef', 'hors-renderer-v5', 'hors-render-v5'):
            self.assertEqual(canonical_selector(parser.parse_args(['build', '--renderer', name]).renderer), hors_v5.NAME)

    def test_frozen_color_frames_preserve_pictures_and_metadata_limits(self):
        frames = [FrameBuild(**f) for f in json.loads(gzip.decompress(
            (ROOT/'tests/fixtures/gmod3/gmod3_metallic_torus-oracle.json.gz').read_bytes()))]
        for encoding in ('literal', 'indexed4'):
            with hors_v5.installed():
                prepared, encode, policy, *_ = hors_v3.encoding_plan(frames, color_encoding=encoding)
            for before, after in zip(frames, prepared):
                self.assertEqual(picture_bytes(before), picture_bytes(after))
                self.assertLessEqual(encode(after)[1], 1024)
                self.assertLessEqual(len(after.clear_spans), 255)
                dirty = {i for i, value in enumerate(picture_bytes(before)[:7680]) if value}
                covered = {i for lo, hi, n in after.clear_spans
                           for i in range(lo+((hi & 127)<<8), lo+((hi & 127)<<8)+n*(1 if hi & 128 else 8))}
                self.assertTrue(dirty <= covered)
                self.assertTrue(all(0 <= i < 7680 for i in covered))
            self.assertFalse(policy['previous_picture_dependency'])

    def test_empty_picture_and_impossible_budget(self):
        empty = FrameBuild([], [(0, 0, 1)], 0, 0, [], [])
        self.assertEqual(hors_v5.plan_clear(empty, 0).clear_spans, [])
        painted = FrameBuild([(0, 0, 2, 0, 0)], [(0, 0, 1)], 2, 2, [], [])
        with self.assertRaisesRegex(ValueError, 'does not fit'):
            hors_v5.plan_clear(painted, 0)

    def test_scoped_hooks_restore_on_error(self):
        plan, staged = hors_v3.encoding_plan, hors_v2_stable.staged
        with self.assertRaisesRegex(RuntimeError, 'test failure'):
            with hors_v5.installed():
                self.assertIsNot(hors_v3.encoding_plan, plan)
                raise RuntimeError('test failure')
        self.assertIs(hors_v3.encoding_plan, plan)
        self.assertIs(hors_v2_stable.staged, staged)

    def test_runtime_patch_does_not_modify_source_files(self):
        for suffix in ('', '-scene'):
            path = ROOT/f'c64/renderer-yunroll-cart-v10{suffix}.asm'
            before = path.read_bytes()
            patched = hors_v5.patch_clear(before.decode())
            self.assertIn('hors_v5_clear_group:', patched)
            self.assertEqual(path.read_bytes(), before)
            with self.assertRaises(ValueError):
                hors_v5.patch_clear(patched.replace('cofs_byte_loop:', 'already_patched:'))


if __name__ == '__main__':
    unittest.main()
