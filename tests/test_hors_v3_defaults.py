"""V3 promotion, fragmented metadata, custom ramps and palette consistency."""
import unittest
from dataclasses import replace
from pathlib import Path
from tools.c643d.hors_v3 import encoding_plan, compact_clear_spans, patch_literal_runtime
from tools.c643d.hors_v2_stable import encoder as v2_encoder
from tools.c643d.cartscene import pack_scene_frames
from tools.c643d.pipeline import FrameBuild
from tools.c643d.optimize import picture_bytes
from tools.c643d.surface_palettes import SHADE_PALETTES, parse_ramp, shade_codes, palette_name
from tools.c643d.surface_fill import quantize, raster
from tools.c643d.colors import C64_PALETTE, nearest_c64_color_index, palette_color_distances
from tools.c643d.mesh import Mesh
from tools.c643d.pipeline import Camera
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


class V3DefaultTests(unittest.TestCase):
    def fragmented(self):
        clear, colors = [], []
        for y in range(24):
            for x in range(0, 32, 2):
                offset = y * 320 + x * 8
                cell = y * 40 + x
                clear.append((offset & 255, (offset >> 8) | 128, 1))
                colors.append((cell & 255, cell >> 8, 1, 0x20 if (x+y) % 3 else 0x50))
        return FrameBuild([], clear, 0, 0, [], colors)

    def test_over_255_spans_are_losslessly_packed_for_180_samples(self):
        frame = self.fragmented()
        with self.assertRaisesRegex(ValueError, '384 clear spans, 384 colour spans'):
            v2_encoder()(frame)
        # Moving colours exercise explicit old-cell reset coverage too.
        frames = [frame, replace(frame, color_spans=[])] * 90
        prepared, encode, policy, literal, runs, palette = encoding_plan(frames)
        self.assertTrue(literal)
        self.assertEqual(policy['clear_metadata_compacted_frames'], 180)
        for old, new in zip(frames, prepared):
            self.assertEqual(picture_bytes(old), picture_bytes(new))
            self.assertEqual(len(new.clear_spans), 24)
        _, directory = pack_scene_frames(prepared, encoder=encode, direct_bytes=True)
        self.assertEqual(len(directory), 180)
        self.assertTrue(all(row['metadata_bytes'] <= 1024 for row in directory))

    def test_clear_expansion_covers_every_old_byte_without_entering_hud(self):
        frame = self.fragmented()
        expanded = compact_clear_spans(frame)
        def covered(f):
            return {i for lo, hi, n in f.clear_spans
                    for i in range(lo + ((hi & 127) << 8), lo + ((hi & 127) << 8) + n * (1 if hi & 128 else 8))}
        before, after = covered(frame), covered(expanded)
        self.assertTrue(before <= after)
        self.assertTrue(all(i < 7680 and i % 320 < 256 for i in after))

    def test_source_frame_is_identified_on_packing_error(self):
        good = FrameBuild([], [], 0, 0, [], [])
        with self.assertRaisesRegex(ValueError, r'scene frame 1 \(sample 2/2\).*384 clear'):
            pack_scene_frames([good, self.fragmented()], encoder=v2_encoder())

    def test_scene_and_object_runtime_accept_same_color_plan(self):
        for suffix in ('', '-scene'):
            source = (ROOT / f'c64/renderer-yunroll-cart-v10{suffix}.asm').read_text()
            patched = patch_literal_runtime(source, [(0, 32), (40, 32)])
            self.assertIn('v3_color_copy:', patched)
            self.assertNotIn('        jsr reset_old_frame_colors', patched)

    def test_all_native_palette_entries_have_named_ramps(self):
        for name in C64_PALETTE:
            self.assertIn(palette_name(name), SHADE_PALETTES)

    def test_custom_ramp_preserves_order_and_repeated_stops(self):
        ramp = parse_ramp('brown,orange,yellow,white')
        self.assertEqual(shade_codes(ramp=ramp), (0, 9, 8, 7, 1))
        mesh = Mesh('face', [(-14,-12,0), (0,14,0), (14,-12,0)], [(0,1,2)])
        for ramp in ((4,4), (0,0), (0,4,14,3,1), tuple(range(16))):
            pic = raster(mesh, Camera(cy=96), 0, 4, shade_ramp=ramp)
            _, _, native = quantize(pic, shade_ramp=ramp)
            self.assertTrue(set(np.unique(native)) <= set((0, *ramp)))

    def test_material_cell_reduction_uses_importer_perceptual_distance(self):
        pic = np.zeros((192,256), dtype=np.uint8)
        values = np.array([0, 5, 5, 5, 9, 9, 13, 13], dtype=np.uint8)
        pic[8:16,8:16] = np.tile(values, (8,1))
        _, screen, result = quantize(pic, preset='material')
        counts = np.bincount(values, minlength=16)
        palette_rgb = {code: rgb for code, rgb in C64_PALETTE.values()}
        distances = np.array([palette_color_distances(palette_rgb[i]) for i in range(16)])
        best = min((sum(counts * np.minimum(distances[:,0], distances[:,hi])), hi)
                   for hi in (5,9,13))[1]
        self.assertEqual(screen[1,1], best << 4)
        for code, rgb in C64_PALETTE.values():
            self.assertEqual(nearest_c64_color_index(rgb), code)


if __name__ == '__main__':
    unittest.main()
