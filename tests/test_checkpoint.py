import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from tools.checkpoint import checkpoint


class CheckpointTests(unittest.TestCase):
    def test_unique_cumulative_and_full_archives_with_checklists(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'repo';root.mkdir();out=Path(td)/'snapshots'
            (root/'VERSION').write_text('0.8.1\n');(root/'code.py').write_text('a=1\n')
            base,_=checkpoint(root,out,completed=['baseline'],validation=['actual baseline check'])
            (root/'code.py').write_text('a=2\n')
            first,report=checkpoint(root,out,baseline=base,completed=['fix'],pending=['native checks'],validation=['unit pass'])
            second,_=checkpoint(root,out,baseline=base)
            self.assertNotEqual(first,second)
            self.assertIn('cp002',first.name);self.assertIn('cp003',second.name)
            with zipfile.ZipFile(first) as z:
                self.assertNotIn('c64-3d-toolkit/VERSION',z.namelist())
                self.assertEqual(z.read('c64-3d-toolkit/code.py'),b'a=2\n')
                entry=next(n for n in z.namelist() if '/docs/checkpoints/' in n)
                record=json.loads(z.read(entry))
                self.assertEqual(record['pending'],['native checks'])
                self.assertEqual(record['validation'],['unit pass'])
            self.assertTrue(first.with_suffix('.zip.sha256').is_file())
            full,_=checkpoint(root,out,baseline=base,full=True)
            with zipfile.ZipFile(full) as z:self.assertIn('c64-3d-toolkit/VERSION',z.namelist())

    def test_config_build_and_external_symlinks_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'repo';root.mkdir();(root/'VERSION').write_text('0.8.1')
            for directory in ('config','build'):(root/directory).mkdir()
            (root/'config/c643d.ini').write_text('private config')
            (root/'build/private.blend').write_text('private source')
            (root/'external').symlink_to(Path(td)/'outside')
            target,_=checkpoint(root,Path(td)/'out')
            with zipfile.ZipFile(target) as z:
                self.assertFalse(any('private' in n or n.endswith('c643d.ini') or n.endswith('external') for n in z.namelist()))
            with self.assertRaises(ValueError):checkpoint(root,root/'out')

if __name__=='__main__':unittest.main()
