"""A release must extract into one checkout and retain executable launchers."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from tools.compile_release import package

class ReleasePackageTests(unittest.TestCase):
    def test_incremental_does_not_overwrite_complete_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'source';root.mkdir()
            (root/'VERSION').write_text('0.7.7\n')
            (root/'unchanged.txt').write_text('keep in the complete release\n')
            baseline=Path(temp)/'baseline.zip';package(root,baseline)
            (root/'VERSION').write_text('0.7.8\n')
            complete=Path(temp)/'c64-3d-toolkit-v0.7.8.zip'
            outputs=package(root,complete,baseline)
            self.assertEqual(len(set(outputs)),2)
            with zipfile.ZipFile(outputs[0]) as z:
                self.assertEqual(set(z.namelist()),{'c64-3d-toolkit/VERSION','c64-3d-toolkit/unchanged.txt'})
                self.assertEqual(z.read('c64-3d-toolkit/VERSION'),b'0.7.8\n')
            with zipfile.ZipFile(outputs[1]) as z:
                self.assertEqual(z.namelist(),['c64-3d-toolkit/VERSION'])

    def test_archive_root_modes_and_local_exclusions(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'source';root.mkdir()
            (root/'VERSION').write_text('0.7.7\n')
            script=root/'RUN-CHECKS.sh';script.write_text('#!/bin/sh\nexit 0\n');script.chmod(0o755)
            (root/'.git').write_text('gitdir: /private/worktree\n')
            for folder in ('build','logs','__pycache__'):
                (root/folder).mkdir();(root/folder/'private.txt').write_text('not for release')
            output=Path(temp)/'release.zip';package(root,output)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(set(z.namelist()),{'c64-3d-toolkit/VERSION','c64-3d-toolkit/RUN-CHECKS.sh'})
                info=z.getinfo('c64-3d-toolkit/RUN-CHECKS.sh')
                self.assertEqual(info.create_system,3)
                self.assertEqual((info.external_attr>>16)&0o777,0o755)
            if shutil.which('unzip'):
                dest=Path(temp)/'unpacked'
                subprocess.run(['unzip','-q',str(output),'-d',str(dest)],check=True)
                self.assertTrue(os.access(dest/'c64-3d-toolkit/RUN-CHECKS.sh',os.X_OK))
