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
            self.assertIn('checkpoint-002',first.name);self.assertIn('checkpoint-003',second.name)
            with zipfile.ZipFile(first) as z:
                self.assertNotIn('c64-3d-toolkit/VERSION',z.namelist())
                self.assertEqual(z.read('c64-3d-toolkit/code.py'),b'a=2\n')
                entry=next(n for n in z.namelist() if '/docs/checkpoints/' in n)
                self.assertEqual(entry,'c64-3d-toolkit/docs/checkpoints/c64-3d-toolkit-v0.8.1-checkpoint-002.json')
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

    def test_numbering_continues_across_legacy_and_new_archives(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'repo';root.mkdir();(root/'VERSION').write_text('0.8.2-dev2')
            out=Path(td)/'out';out.mkdir()
            legacy=out/'c64-3d-toolkit-v0.8.1-cp007-incremental.zip'
            legacy.write_bytes(b'preserved legacy archive')
            (out/'c64-3d-toolkit-v0.8.2-dev1-checkpoint-009-full.zip').write_bytes(b'preserved new archive')
            (out/'c64-3d-toolkit-v0.8.1-cp999-notes.zip').write_bytes(b'not a checkpoint')
            target,report=checkpoint(root,out)
            self.assertIn('checkpoint-010',target.name)
            self.assertEqual(report['checkpoint'],10)
            self.assertEqual(legacy.read_bytes(),b'preserved legacy archive')

    def test_applied_records_continue_numbering_in_a_new_destination(self):
        for label in ('cp001','checkpoint-001'):
            with self.subTest(label=label),tempfile.TemporaryDirectory() as td:
                root=Path(td)/'repo';root.mkdir();(root/'VERSION').write_text('0.8.2-dev2')
                records=root/'docs/checkpoints';records.mkdir(parents=True)
                record=records/f'c64-3d-toolkit-v0.8.2-dev1-{label}.json'
                record.write_text('{"checkpoint": 1}\n')
                target,report=checkpoint(root,Path(td)/'new-output')
                self.assertIn('checkpoint-002',target.name)
                self.assertEqual(report['checkpoint'],2)
                self.assertEqual(record.read_text(),'{"checkpoint": 1}\n')

if __name__=='__main__':unittest.main()
