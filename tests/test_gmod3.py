"""GMod3 boundaries and CLI isolation; hardware behavior is checked in VICE."""
import struct
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from tools.c643d import gmod3_image as image
from tools.c643d.cartridge_defaults import resolve
from tools.c643d.gmod3_stream import pack_frames, emit_directory
from tools.c643d.gmod3_v3 import capacity_screen
from tools.c643d.pipeline import FrameBuild
from tools.c643d.cli import make_parser
from tools.c643d.toolchain import load_toolchain_settings


def crt_bytes(size_mib=2):
    header = bytearray(64)
    header[:16] = b'C64 CARTRIDGE   '
    struct.pack_into('>IHH', header, 16, 64, 0x100, 62)
    header[25] = 1
    banks = []
    for bank in range(image.bank_count(size_mib)):
        data = bytearray(8192)
        if bank == 0:
            data[:9] = bytes.fromhex('0c 80 0c 80 c3 c2 cd 38 30')
        banks.append(struct.pack('>4sIHHHH', b'CHIP', 8208, 0, bank, 0x8000, 8192)+data)
    return header+b''.join(banks)


class GMod3Tests(unittest.TestCase):
    def test_full_bank_addressing_and_capacity_edges(self):
        for capacity in image.CAPACITIES_MIB:
            n = image.bank_count(capacity)
            for bank in range(n):
                address, value = image.bank_select(bank, capacity)
                self.assertEqual((address-0xde00)*256+value, bank)
            for bank in (-1, n, 2048, True):
                with self.assertRaises(ValueError):
                    image.bank_select(bank, capacity)
        for size in (0, 1, 3, 32, 2.0):
            with self.assertRaises(ValueError):
                image.new_image(size)

    def test_bank_write_rejects_crossing_without_resizing_image(self):
        raw = image.new_image(2)
        image.put_bank(raw, 255, b'END', 8189)
        self.assertEqual(raw[-3:], b'END')
        for bank, payload, offset in [(256, b'x', 0), (1, b'xx', 8191), (1, b'x', -1)]:
            with self.assertRaises(ValueError):
                image.put_bank(raw, bank, payload, offset)
        self.assertEqual(len(raw), 2*1024*1024)

    def test_pack_crosses_255_and_1023_without_truncating(self):
        f = FrameBuild([], [], 0, 0, [])
        for capacity, first in ((4,255),(8,511),(16,1023),(16,2046)):
            raw, directory = pack_frames([f]*2, size_mib=capacity, first_bank=first,
                encode=lambda f,c: (b'Q'*8192, 0))
            self.assertEqual([d['bank'] for d in directory], [first, first+1])
            self.assertEqual(raw[(first+1)*8192:(first+2)*8192], b'Q'*8192)
        with self.assertRaises(ValueError):
            pack_frames([f]*2, size_mib=2, first_bank=255, encode=lambda f,c:(b'Q'*8192,0))
        with self.assertRaises(ValueError):
            pack_frames([f]*256)
        with self.assertRaises(ValueError):
            pack_frames([f], first_bank=3)

    def test_crt_roundtrip_structure_and_corruption(self):
        good = crt_bytes()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'test.crt'
            path.write_bytes(good)
            self.assertEqual(image.inspect_crt(path)['bank_count'], 256)
            cases = [good[:-1], good[:63], good+good[64:8272]]
            for offset, value in ((23,32),(24,1),(25,0),(26,1),(31,1),(64+12,0xa0),(64+16+4,0)):
                bad = bytearray(good); bad[offset] = value; cases.append(bad)
            for bad in cases:
                path.write_bytes(bad)
                with self.assertRaises(ValueError):
                    image.inspect_crt(path)

    def test_defaults_and_separate_explicit_hardware_choice(self):
        parser = make_parser(load_toolchain_settings(None))
        for command in ('build', 'cartridge-smoke'):
            self.assertEqual(resolve(parser.parse_args([command]),None), 'gmod3' if command=='build' else 'easyflash')
            self.assertEqual(parser.parse_args([command, '--cart-type', 'gmod3']).cart_type, 'gmod3')
        self.assertEqual(parser.parse_args(['build']).renderer, 'hors-v4')
        self.assertEqual(parser.parse_args(['build','--cart-type','gmod3']).renderer, 'hors-v4')

    def test_configured_cart_default_and_cli_override(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'user.ini'
            for setting,expected in [('auto','gmod3'),('easyflash','easyflash'),('gmod3','gmod3')]:
                path.write_text('[cartridge_defaults]\ncart_type = '+setting+'\n')
                parser=make_parser(load_toolchain_settings(path))
                self.assertEqual(resolve(parser.parse_args(['build']),load_toolchain_settings(path)),expected)
                self.assertEqual(resolve(parser.parse_args(['build','--renderer','hors-renderer-v3']),load_toolchain_settings(path)), 'easyflash' if setting=='auto' else expected)
                self.assertEqual(parser.parse_args(['build','--cart-type','easyflash']).cart_type,'easyflash')
                self.assertEqual(parser.parse_args(['build','--cart-type','gmod3']).cart_type,'gmod3')
                for command in ('doctor','list-shapes','cart-demos'):
                    self.assertEqual(resolve(parser.parse_args([command]),load_toolchain_settings(path)), 'easyflash')
                self.assertEqual(resolve(parser.parse_args(['build','--renderer','yunroll']),load_toolchain_settings(path)), 'easyflash')

    def test_cli_routes_default_v4_and_preserved_explicit_easyflash(self):
        from tools.c643d import cli
        from tools.c643d import hors_v4, gmod3_cli
        with patch.object(hors_v4,'build',return_value=41) as v4, \
             patch.object(gmod3_cli,'build',return_value=42) as gm, \
             patch.object(cli,'cmd_build',return_value=43) as ef:
            self.assertEqual(cli.main(['build','--no-config']),41)
            self.assertEqual(cli.main(['cart-stream','--no-config','--renderer','hors-render-v4']),41)
            self.assertEqual(cli.main(['build','--no-config','--renderer','hors-renderer-v3']),43)
            self.assertEqual(cli.main(['build','--no-config','--cart-type','easyflash']),43)
            self.assertEqual(cli.main(['build','--no-config','--renderer','hors-renderer-v3','--cart-type','gmod3']),42)
            self.assertEqual((v4.call_count,gm.call_count,ef.call_count),(2,1,2))

    def test_short_aliases_and_explicit_hardware_suffixes(self):
        from tools.c643d.renderer_names import canonical_selector, display_name
        parser=make_parser(load_toolchain_settings(None))
        expected={1:'hors-render-v1',2:'hors-render-v2',3:'hors-renderer-v3',4:'hors-renderer-v4'}
        for version,name in expected.items():
            for alias in (f'hors-v{version}',f'hors-renderer-v{version}'):
                args=parser.parse_args(['build','--renderer',alias])
                self.assertEqual(canonical_selector(args.renderer),name)
                self.assertEqual(resolve(args,None),'gmod3' if version==4 else 'easyflash')
        for alias,cart in [('hors-v4-ef','easyflash'),('hors-v4-gmod3','gmod3')]:
            args=parser.parse_args(['build','--renderer',alias])
            self.assertEqual(resolve(args,None),cart)
            self.assertEqual(display_name(canonical_selector(alias),cart),alias)
            args.cart_type='gmod3' if cart=='easyflash' else 'easyflash'
            with self.assertRaises(ValueError):resolve(args,None)

    def test_capacity_accounting_and_maximum_width(self):
        for size in image.CAPACITIES_MIB:
            for used in (1, image.bank_count(size)-4):
                src, report = capacity_screen('build_screen_visible:\n', size,
                    [dict(bank=bank) for bank in range(4,4+used)])
                self.assertEqual(report['used_bytes']+report['free_bytes'], size*1024*1024)
                for line in report['lines']:
                    self.assertLessEqual(len(line['text']), 40)
                    self.assertEqual(line['column'], (40-len(line['text']))//2)
                self.assertIn('jsr gmod3_capacity_screen', src)


if __name__ == '__main__':
    unittest.main()
