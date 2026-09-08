import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from tools.clean_release import clean


class ReleaseCleanupTests(unittest.TestCase):
    def test_preserves_local_bytes_and_references_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp) / 'project'
            removed = {
                'examples/old/custom-edited.crt': b'local edit, keep this in archive',
                'examples/cart_demos/c643d-demo-v0.6.7-rc5-yunroll-cart-v7-all.crt': b'rc5',
                'examples/cart_demos/c643d-demo-v0.6.5-yunroll-cart-v4-all.crt': b'build reference',
                'examples/cart_demos/c643d-demo-v0.6.7-rc3-yunroll-cart-v6-all.crt': b'comparison',
                'examples/blender_horse_and_sunflower/preview.mp4': b'video',
                'examples/blender_horse_and_sunflower/scene.blend1': b'backup',
            }
            kept = {
                'examples/cart_demos/c643d-demo-v0.6.7-yunroll-cart-v7-all.crt': b'final',
                'examples/cart_demos/metadata/c643d-demo-v0.6.7-yunroll-cart-v7-all-cart-manifest.json': b'metadata',
                'examples/blender_horse_and_sunflower/scene.blend': b'editable scene',
                'examples/blender_horse_and_sunflower/preview.png': b'documented still',
            }
            for name, data in (removed | kept).items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            target = Path(temp) / 'legacy.zip'
            self.assertEqual(clean(root, target, True, scope="legacy-0.6.7")['files'], len(removed))
            self.assertFalse(target.exists())
            result = clean(root, target, scope="legacy-0.6.7")
            self.assertEqual(result['files'], len(removed))
            with ZipFile(target) as archive:
                self.assertEqual({name: archive.read(name) for name in archive.namelist()}, removed)
            for name, data in kept.items():
                self.assertEqual((root / name).read_bytes(), data)
            self.assertFalse((root / 'examples/old').exists())
            self.assertEqual(clean(root, target, scope="legacy-0.6.7")['files'], 0)

    def test_existing_archive_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp) / 'project'
            old = root / 'examples/old/local.crt'
            old.parent.mkdir(parents=True)
            old.write_bytes(b'new local bytes')
            target = Path(temp) / 'legacy.zip'
            target.write_bytes(b'existing backup')
            result = clean(root, target, scope="legacy-0.6.7")
            self.assertNotEqual(result['archive'], str(target))
            self.assertEqual(target.read_bytes(), b'existing backup')
            with ZipFile(result['archive']) as archive:
                self.assertEqual(archive.read('examples/old/local.crt'), b'new local bytes')

    def test_rejects_archive_inside_repository_and_symlink_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'project'
            old = root / 'examples/old/local.crt'
            old.parent.mkdir(parents=True)
            old.write_bytes(b'data')
            with self.assertRaisesRegex(ValueError, 'outside'):
                clean(root, root / 'legacy.zip', scope='legacy-0.6.7')
            old.unlink()
            external = Path(temp) / 'outside.crt'
            external.write_bytes(b'outside')
            old.symlink_to(external)
            with self.assertRaisesRegex(ValueError, 'non-regular'):
                clean(root, scope="legacy-0.6.7")
            self.assertEqual(external.read_bytes(), b'outside')


class V068CleanupTests(unittest.TestCase):
    def test_default_archives_only_rc1_and_preserves_comparisons(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp)/'repo'
            old = 'examples/cart_demos/c643d-demo-v0.6.8-rc1-yunroll-cart-v8-all'
            removed = {old+'.crt': b'local rc1 edits', old+'-ram.crt': b'ram',
                'examples/cart_demos/metadata/c643d-demo-v0.6.8-rc1-yunroll-cart-v8-all-cart-manifest.json': b'meta'}
            kept = {'examples/cart_demos/c643d-demo-v0.6.8-yunroll-cart-v8-all.crt': b'final',
                'examples/cart_demos/c643d-demo-v0.6.7-yunroll-cart-v7-all.crt': b'v7',
                'examples/cart_demos/c643d-demo-v0.6.7-rc3-yunroll-cart-v6-all.crt': b'v6',
                'examples/old/local.crt': b'older', 'examples/custom.mp4': b'video'}
            for name, data in (removed|kept).items():
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            self.assertEqual(clean(root,dry_run=True)['files'],3)
            self.assertTrue((root/(old+'.crt')).exists())
            result=clean(root)
            self.assertEqual(result['files'],3)
            with ZipFile(result['archive']) as z:
                self.assertEqual({n:z.read(n) for n in z.namelist()},removed)
            for name,data in kept.items():self.assertEqual((root/name).read_bytes(),data)
            self.assertEqual(clean(root)['files'],0)

    def test_rc1_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'repo';cart=root/'examples/cart_demos/c643d-demo-v0.6.8-rc1-yunroll-cart-v8-all.crt'
            cart.parent.mkdir(parents=True);outside=Path(temp)/'original.crt';outside.write_bytes(b'keep')
            cart.symlink_to(outside)
            with self.assertRaisesRegex(ValueError,'non-regular'):clean(root)
            self.assertEqual(outside.read_bytes(),b'keep')
