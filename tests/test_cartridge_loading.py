import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.c643d.cartridge import (
    easyapi_bytes, easyflash_offset, inspect_easyflash_crt,
    install_easyflash_metadata, install_scene_extension, new_easyflash_image,
    petscii_title, put_easyflash_chip,
)
from tools.c643d.cartlaunch import command


def bootstrap():
    data = bytearray(b'\xff' * 8192)
    data[0] = 0x78
    data[-6:] = b'\x00\xe0' * 3
    return bytes(data)


def crt_bytes(romh):
    header = bytearray(64)
    header[:16] = b'C64 CARTRIDGE   '
    struct.pack_into('>IHH', header, 16, 64, 0x100, 32)
    header[24] = 1
    header[32:36] = b'TEST'
    return bytes(header) + struct.pack('>4sIHHHH', b'CHIP', 8208, 2, 0, 0xA000, 8192) + romh


class CartridgeLoadingTests(unittest.TestCase):
    def test_name_uses_reference_petscii_bytes(self):
        # The Programmer's Reference chapter 6 explicitly gives Myth as these bytes.
        self.assertEqual(petscii_title('Myth'), bytes.fromhex('6d 59 54 48') + b'\0' * 12)
        self.assertEqual(len(petscii_title('A' * 40)), 16)
        self.assertNotIn(0, petscii_title('A' * 40))

    def test_metadata_real_driver_and_idempotent_conversion(self):
        image = new_easyflash_image()
        put_easyflash_chip(image, 0, 'romh', bootstrap())
        before = bytes(image)
        install_easyflash_metadata(image, 'Myth')
        base = easyflash_offset(0, 'romh')
        self.assertEqual(image[base + 0x1800:base + 0x1B00], easyapi_bytes())
        self.assertEqual(image[base + 0x1B00:base + 0x1B08], bytes.fromhex('65 66 2d 6e 41 4d 45 3a'))
        changed = [i for i, (a, b) in enumerate(zip(before, image)) if a != b]
        self.assertTrue(all(base + 0x1800 <= i < base + 0x1B18 for i in changed))
        expected = bytes(image)
        install_easyflash_metadata(image, 'Myth')
        self.assertEqual(image, expected)

    def test_metadata_never_stamps_over_zero_or_other_payload(self):
        for value in (0, 0x60, 0x12):
            image = new_easyflash_image()
            image[easyflash_offset(0, 'romh', 0x1800)] = value
            before = bytes(image)
            with self.assertRaisesRegex(ValueError, 'overlaps'):
                install_easyflash_metadata(image, 'TEST')
            self.assertEqual(image, before)

    def test_scene_relocation_restores_every_extension_byte(self):
        for size in (0, 0x1400, 0x1A00, 0x1BFA):
            image = new_easyflash_image()
            for bank in range(3):
                put_easyflash_chip(image, bank, 'roml', bytes(8192))
            extension = bytes((i * 19 + 7) & 255 for i in range(size))
            original = bytearray(bootstrap())
            original[0x400:0x400 + size] = extension
            install_scene_extension(image, bootstrap(), extension)
            install_easyflash_metadata(image, 'SCENE')
            base = easyflash_offset(0, 'romh')
            loaded = bytearray(image[base + 0x400:base + 0x2000])
            spill = easyflash_offset(2, 'roml', 0x1800)
            loaded[0x1400:0x1800] = image[spill:spill + 0x400]
            self.assertEqual(loaded, original[0x400:0x2000])
            self.assertEqual(image[base + 0x1FFA:base + 0x2000], bootstrap()[-6:])
        with self.assertRaisesRegex(ValueError, 'reset vectors'):
            install_scene_extension(image, bootstrap(), bytes(0x1BFB))

    def test_scene_relocation_rejects_occupied_spare_space(self):
        image = new_easyflash_image()
        with self.assertRaisesRegex(ValueError, 'ROML bank 2 tail'):
            install_scene_extension(image, bootstrap(), b'')

    def test_crt_parser_accepts_old_carts_but_requires_metadata_for_new(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'demo.crt'
            p.write_bytes(crt_bytes(bootstrap()))
            self.assertFalse(inspect_easyflash_crt(p)['eapi_present'])
            with self.assertRaisesRegex(ValueError, 'cartridge-name'):
                inspect_easyflash_crt(p, require_metadata=True)
            image = new_easyflash_image()
            put_easyflash_chip(image, 0, 'romh', bootstrap())
            install_easyflash_metadata(image, 'TEST')
            p.write_bytes(crt_bytes(image[8192:16384]))
            self.assertTrue(inspect_easyflash_crt(p, require_metadata=True)['eapi_present'])

    def test_crt_parser_rejects_corruption(self):
        good = crt_bytes(bootstrap())
        cases = [good[:20], good[:-1], good + good[64:]]
        bad_id = bytearray(good); bad_id[23] = 0; cases.append(bad_id)
        bad_vector = bytearray(good); bad_vector[-4:-2] = b'\x00\xf8'; cases.append(bad_vector)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'demo.crt'
            for case in cases:
                p.write_bytes(case)
                with self.assertRaises(ValueError):
                    inspect_easyflash_crt(p)

    def test_launcher_options_preserve_preferences_but_protect_files(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'cart with spaces.crt'; p.write_bytes(crt_bytes(bootstrap()))
            argv = command('x64sc', p, ['-warp', '-ntsc', '-easyflashcrtwrite', '-saveres'])
            self.assertNotIn('-default', argv)
            self.assertGreater(argv.index('-warp'), argv.index('+warp'))
            self.assertGreater(argv.index('-ntsc'), argv.index('-pal'))
            self.assertEqual(argv[-5:], ['+saveres', '+easyflashcrtwrite', '+cart', '-cartcrt', str(p)])
            self.assertEqual(command('x64sc', p, clean_settings=True)[1], '-default')
            self.assertIn('+saveres', command('x64sc', p, clean_settings=True))
            headless = command('x64sc', p, ['-console'], clean_settings=True)
            self.assertEqual(headless[1], '-console')
            self.assertNotIn('+VICIIfull', headless)

    def test_run_cart_cli_propagates_recovery_and_exit_status(self):
        from tools.c643d.cli import main
        with patch('tools.c643d.cli.resolve_executable', return_value='x64sc'), \
                patch('tools.c643d.cli.run_cartridge', return_value=5) as run:
            result = main(['run-cart', 'demo.crt', '--no-config', '--vice-clean-settings', '--vice-arg=-warp'])
        self.assertEqual(result, 5)
        self.assertTrue(run.call_args.kwargs['clean_settings'])
        self.assertEqual(run.call_args.args[2], ['-warp'])


if __name__ == '__main__':
    unittest.main()
