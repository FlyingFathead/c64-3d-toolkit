import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from tools.archive_old_carts import archive
from tools.c643d.prgframes import extract
from tools.c643d.toolchain import load_toolchain_settings
from tools.c643d.cli import CARTRIDGE_DEMO_ENTRIES, make_parser


class UniformCartTests(unittest.TestCase):
    def test_canonical_frames_preserve_authored_counts(self):
        expected = [32, 32, 36, 24, 32, 28, 20, 24, 32, 18]
        for (_, path), count in zip(CARTRIDGE_DEMO_ENTRIES, expected):
            frames, colors, screen, hud, text = extract(path)
            self.assertEqual(len(frames), count, path)
            self.assertGreater(len(hud), 0)
            self.assertTrue(all(f.records for f in frames), path)

    def test_corrupt_clear_coverage_is_rejected(self):
        path = CARTRIDGE_DEMO_ENTRIES[0][1]
        data = bytearray(path.read_bytes())
        load = int.from_bytes(data[:2], 'little')
        data[2 + 0x4803 - load] = 0  # Invalid first clear span length.
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / 'corrupt.prg'
            bad.write_bytes(data)
            with self.assertRaises(ValueError):
                extract(bad)

    def test_default_and_explicit_comparison_renderer(self):
        parser = make_parser(load_toolchain_settings(Path("/definitely/missing/c643d.ini")))
        self.assertEqual(parser.parse_args(['cart-demos']).stream_renderer,
                         'yunroll-cart-v4')
        self.assertEqual(parser.parse_args(['cart-demos', '--stream-renderer',
                                          'yunroll-cart-v3']).stream_renderer,
                         'yunroll-cart-v3')

    def test_archive_overlay_preserves_local_changes_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp)
            source = root / 'examples/cart_demos'
            target = root / 'examples/old/cart_demos'
            source.mkdir(parents=True)
            target.mkdir(parents=True)
            (source / 'c643d-demo.crt').write_bytes(b'local edit')
            (target / 'c643d-demo.crt').write_bytes(b'archive from ZIP')
            (source / 'c643d-demo-v0.6.4.crt').write_bytes(b'identical')
            (target / 'c643d-demo-v0.6.4.crt').write_bytes(b'identical')
            (source / 'my-cart.crt').write_bytes(b'custom')
            self.assertEqual(archive(root, dry_run=True), 2)
            self.assertTrue((source / 'c643d-demo.crt').exists())
            self.assertEqual(archive(root), 2)
            self.assertEqual(archive(root), 0)
            self.assertEqual((target / 'c643d-demo.crt').read_bytes(), b'archive from ZIP')
            self.assertEqual(next(target.glob('*-local-*')).read_bytes(), b'local edit')
            self.assertEqual((source / 'my-cart.crt').read_bytes(), b'custom')


if __name__ == '__main__':
    unittest.main()
