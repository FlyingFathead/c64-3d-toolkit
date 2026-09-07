import unittest
from dataclasses import replace
from tools.c643d.pipeline import FrameBuild, oriented_dda, encode_run, choose_dda
from tools.c643d.optimize import remove_redundant_runs, optimize_frames, picture_bytes
from tools.c643d.cartscene import pack_scene_frames
from tools.c643d.cartstream import frame_block


def run(a, b):
    dda = oriented_dda(*a, *b)
    return encode_run(dda, 0, len(dda['points'])-1)


def frame(records, colors=None):
    return FrameBuild(records, [(0, 0, 2)], sum(r[2] for r in records), 0, [], colors or [(0, 0, 2, 16)])


class V5OptimizationTests(unittest.TestCase):
    def test_cover_witness_prevents_mutual_deletion(self):
        full = run((0, 0), (15, 0))
        left = run((0, 0), (7, 0))
        right = run((8, 0), (15, 0))
        source = frame([left, right, full, full, left])
        result = remove_redundant_runs(source)
        self.assertEqual(result.records, [full])
        self.assertEqual(picture_bytes(result), picture_bytes(source))
        self.assertEqual(result.color_spans, source.color_spans)
        self.assertEqual(result.clear_spans, source.clear_spans)
        self.assertEqual(remove_redundant_runs(result), result)

    def test_partial_overlap_is_not_deleted(self):
        a = run((0, 0), (9, 0))
        b = run((6, 0), (15, 0))
        self.assertEqual(remove_redundant_runs(frame([a, b])).records, [a, b])

    def test_picture_identity_includes_resolved_colors(self):
        a = frame([run((0, 0), (15, 0))])
        b = replace(a, color_spans=[(0, 0, 2, 32)])
        c = frame([run((0, 0), (7, 0)), run((8, 0), (15, 0))])
        result, stats = optimize_frames([a, a, b, c])
        self.assertEqual(stats['picture_references'], [0, 0, 2, 0])
        self.assertEqual(stats['consecutive_holds'], 1)
        self.assertEqual(stats['unique_pictures'], 2)
        image, directory = pack_scene_frames(result, aliases=stats['picture_references'])
        self.assertEqual(directory[0]['address'], directory[3]['address'])
        self.assertNotEqual(directory[0]['address'], directory[2]['address'])
        self.assertEqual(directory[3]['frame'], 3)
        self.assertEqual(directory[3]['reference_frame'], 0)
        self.assertEqual(directory[0]['sha256'], directory[3]['sha256'])

    def test_empty_frame_and_color_only_changes(self):
        a = FrameBuild([], [], 0, 0, [], [])
        b = replace(a, color_spans=[(0, 0, 1, 32)])
        _, stats = optimize_frames([a, a, b, b, a])
        self.assertEqual(stats['picture_references'], [0, 0, 2, 2, 0])
        self.assertEqual(stats['consecutive_holds'], 2)

    def test_directory_references_across_page_boundary(self):
        a = frame([run((0, 0), (15, 0))])
        fs = [a]*513
        _, directory = pack_scene_frames(fs, aliases=[0]*513)
        self.assertEqual(len(directory), 513)
        self.assertEqual(len({(d['bank'], d['address']) for d in directory}), 1)
        self.assertEqual(directory[512]['frame'], 512)

    def test_dda_cache_returns_original_result(self):
        choose_dda.cache_clear()
        for major, minor in [(0,0), (127,0), (31,7), (63,32), (127,126)]:
            self.assertEqual(choose_dda(major, minor), choose_dda.__wrapped__(major, minor))
            self.assertEqual(choose_dda(major, minor), choose_dda.__wrapped__(major, minor))
        self.assertEqual(choose_dda.cache_info().hits, 5)


if __name__ == '__main__':
    unittest.main()
