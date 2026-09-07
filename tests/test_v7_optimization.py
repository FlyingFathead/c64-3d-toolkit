"""Lossless V7 transformations and explicit speed/RAM preference boundaries."""
from dataclasses import replace
import unittest
from itertools import product
from tools.c643d.pipeline import FrameBuild, oriented_dda, encode_run, decode_record_points
from tools.c643d.optimize import picture_bytes
from tools.c643d.runjoin import join_frames, join_frame_runs
from tools.c643d.clearplan import selective_clear, BYTE_RANGE
from tools.c643d.preferences import apply_preference
from tools.c643d.cli import make_parser
from tools.c643d.toolchain import load_toolchain_settings
from pathlib import Path


def run(a, b):
    dda = oriented_dda(*a, *b)
    return encode_run(dda, 0, len(dda['points']) - 1)


def frame(records, spans=None):
    points = {p for rec in records for p in decode_record_points(rec)}
    cells = sorted({(y//8)*320 + (x//8)*8 for x, y in points})
    return FrameBuild(records, spans if spans is not None else [(o&255, o>>8, 1) for o in cells],
                      sum(rec[2] for rec in records), len(points), [],
                      [(o//8&255, o//8>>8, 1, 112) for o in cells])


class V7OptimizationTests(unittest.TestCase):
    def test_join_keeps_exact_path_and_resolved_colours(self):
        for axis, negative, shared in product((0,1),(False,True),(False,True)):
            path = [(16+i, 48+(-1 if negative else 1)*(i//2)) for i in range(20)]
            if axis:
                path = [(y, x) for x, y in path]
            a, b = path[:10], path[9 if shared else 10:]
            records = [encode_run(dict(axis=axis, negative=negative, points=p), 0, len(p)-1) for p in (a,b)]
            source = frame(records)
            result, stats = join_frame_runs(source)
            assert len(result.records) == 1 and stats['merged_runs'] == 1
            assert decode_record_points(result.records[0]) == path
            assert picture_bytes(result) == picture_bytes(source)
            assert result.color_spans == source.color_spans
            assert result.clear_spans == source.clear_spans


    def test_join_does_not_bridge_pixel_gaps(self):
        for end, start in [((9,4),(11,4)),((9,4),(10,6))]:
            source = frame([run((0,4),end),run(start,(18,start[1]))])
            result, _ = join_frames([source])
            assert len(result[0].records) == 2
            assert picture_bytes(result[0]) == picture_bytes(source)


    def test_join_keeps_direction_changes_and_127_pixel_limit(self):
        source = frame([run((0,0),(7,7)), run((7,7),(14,0))])
        assert len(join_frames([source])[0][0].records) == 2
        source = frame([run((0,0),(125,0)),run((126,0),(127,0))])
        assert len(join_frames([source])[0][0].records) == 2  # 128 pixels exceed one header
        source = frame([run((0,0),(124,0)),run((125,0),(126,0))])
        result, _ = join_frames([source])
        assert len(result[0].records) == 1 and result[0].records[0][2] == 127


    def test_position_order_finds_chain_in_reverse_input_and_is_deterministic(self):
        source = frame([run((16,0),(23,0)),run((8,0),(15,0)),run((0,0),(7,0))])
        result, stats = join_frames([source])
        assert len(result[0].records) == 1 and stats['merged_runs'] == 2
        assert (result, stats) == join_frames([source])
        assert picture_bytes(result[0]) == picture_bytes(source)


    def test_selective_clear_covers_every_dirty_byte_without_growing_metadata(self):
        source = frame([run((0,3),(31,3)),run((48,12),(48,19))])
        result, stats = selective_clear(source)
        covered = set()
        for lo, hi, n in result.clear_spans:
            start = lo + ((hi & ~BYTE_RANGE) << 8)
            covered.update(range(start, start + (n if hi & BYTE_RANGE else n*8)))
        dirty = {(y//8)*320 + (x//8)*8 + (y&7) for rec in source.records for x,y in decode_record_points(rec)}
        assert dirty <= covered
        assert len(result.clear_spans) == len(source.clear_spans)
        assert stats['metadata_bytes_added'] == 0 and stats['byte_spans'] > 0
        assert stats['selected_clear_bytes'] < stats['original_clear_bytes']
        assert picture_bytes(result) == picture_bytes(source)


    def test_dense_cells_keep_cell_clearing_and_no_viewport_crossing(self):
        source = frame([run((0,0),(0,7))])
        result, stats = selective_clear(source)
        assert result.clear_spans == source.clear_spans and stats['byte_spans'] == 0
        with self.assertRaises(ValueError):
            selective_clear(replace(source, clear_spans=[(0xff,0x1d,32)]))


    def test_fps_default_and_ram_validation(self):
        parser = make_parser(load_toolchain_settings(Path('/missing/c643d.ini')))
        for command in ('build','cart-demos','cartridge-demo'):
            assert parser.parse_args([command]).prefer == 'fps'
        args = parser.parse_args(['cart-demos','--stream-renderer','yunroll-cart-v7'])
        assert args.play_all_seconds == 10
        assert parser.parse_args(['cart-demos','--play-all-seconds','25']).play_all_seconds == 25
        assert apply_preference('PREFER_RAM = 0', 'yunroll-cart-v7') == 'PREFER_RAM = 0'
        assert apply_preference('PREFER_RAM = 0', 'yunroll-cart-v7', 'ram') == 'PREFER_RAM = 1'
        with self.assertRaises(ValueError):
            apply_preference('', 'yunroll-cart-v6', 'ram')
        with self.assertRaises(ValueError):
            apply_preference('', 'yunroll-cart-v7', 'ram')
