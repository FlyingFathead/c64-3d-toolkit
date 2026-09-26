import gzip
import json
from pathlib import Path
import unittest
from tools.c643d import hors_v5_c2 as c2, hors_v3, hors_v2_stable
from tools.c643d.pipeline import FrameBuild
from tools.c643d.optimize import picture_bytes
from tools.c643d.renderer_names import canonical_selector, DEFAULT_RENDERER
from tools.c643d.cli import make_parser
from tools.c643d.toolchain import load_toolchain_settings

ROOT = Path(__file__).resolve().parents[1]


class CandidateTwo(unittest.TestCase):
    def test_names_keep_c1_and_default(self):
        parser = make_parser(load_toolchain_settings(None))
        for name in ['hors-v5', 'hors-v5-c1', 'hors-v5-c1-ef']:
            self.assertEqual(canonical_selector(parser.parse_args(['build', '--renderer', name]).renderer), 'hors-renderer-v5')
        for name in ['hors-v5-c2', 'hors-v5-c2-ef']:
            self.assertEqual(canonical_selector(parser.parse_args(['build', '--renderer', name]).renderer), c2.NAME)
        self.assertEqual(DEFAULT_RENDERER, 'hors-v4')

    def test_both_transports_preserve_full_colour_pictures(self):
        original = [FrameBuild(**f) for f in json.loads(gzip.decompress(
            (ROOT/'tests/fixtures/gmod3/gmod3_metallic_torus-oracle.json.gz').read_bytes()))]
        for mode in ['runs', 'shared', 'auto']:
            frames, encode, policy, *_ = c2.encoding_plan(original, mode=mode)
            self.assertIn(policy['c2_color_plan'], ['runs', 'shared'])
            for before, after in zip(original, frames):
                self.assertEqual(picture_bytes(before), picture_bytes(after))
                self.assertLessEqual(encode(after)[1], 1024)
                self.assertLessEqual(len(encode(after)[0]), 8192)

    def test_context_preserves_old_reset_only_for_runs_and_restores(self):
        frames = [FrameBuild([(0, 0, 2, 0, 0)], [(0, 0, 1)], 2, 2, [], [(0, 0, 1, 32)])]
        plan, stage, patch = hors_v3.encoding_plan, hors_v2_stable.staged, hors_v3.patch_runtime
        runtime = (ROOT/'c64/renderer-yunroll-cart-v10-scene.asm').read_text()
        for mode in ['runs', 'shared']:
            with self.assertRaisesRegex(RuntimeError, 'restore'):
                with c2.installed(mode):
                    hors_v3.encoding_plan(frames)
                    changed = hors_v3.patch_runtime(runtime)
                    self.assertEqual('jsr reset_old_frame_colors' in changed, mode == 'runs')
                    raise RuntimeError('restore')
            self.assertIs(hors_v3.encoding_plan, plan)
            self.assertIs(hors_v2_stable.staged, stage)
            self.assertIs(hors_v3.patch_runtime, patch)


if __name__ == '__main__':
    unittest.main()
