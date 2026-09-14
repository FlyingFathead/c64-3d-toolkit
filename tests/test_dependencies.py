import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from tools.c643d import dependencies as deps

ROOT = Path(__file__).resolve().parents[1]


class DependencyTests(unittest.TestCase):
    def test_clean_exit_in_python_without_site_packages(self):
        for command in (['build','--blend','missing.blend'], ['build','--shape','cube'], ['dependencies','--svg']):
            r = subprocess.run([sys.executable,'-S',str(ROOT/'c643d.py'),*command], cwd=ROOT, capture_output=True,text=True)
            self.assertEqual(r.returncode,2,r.stderr)
            self.assertNotIn('Traceback',r.stdout+r.stderr)
            self.assertIn('numpy',r.stdout+r.stderr)
            self.assertIn('Pillow',r.stdout+r.stderr)
            self.assertIn('setup-python.py',r.stdout+r.stderr)
        for command in (['--help'], ['--version'], ['list-shapes']):
            r = subprocess.run([sys.executable,'-S',str(ROOT/'c643d.py'),*command],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)

    def test_requirement_files_cover_core_and_svg_imports(self):
        self.assertEqual({n.lower() for n,b in deps.requirements()}, {'numpy','pillow'})
        self.assertEqual({n.lower() for n,b in deps.requirements(True)}, {'numpy','pillow','cairosvg','defusedxml'})

    def test_version_bounds_and_broken_native_library(self):
        self.assertTrue(deps.satisfies('1.24.0','>=1.24'))
        self.assertFalse(deps.satisfies('1.24.0rc1','>=1.24'))
        self.assertFalse(deps.satisfies('1.23.9','>=1.24'))
        self.assertFalse(deps.satisfies('3.0','>=2.9.1,<3'))
        output=io.StringIO()
        with patch.object(deps.metadata,'version',return_value='99.0'), patch.object(deps.importlib,'import_module',side_effect=OSError('native DLL failed')):
            self.assertFalse(deps.check(stream=output))
        self.assertIn('native DLL failed',output.getvalue())
        self.assertIn('--repair',output.getvalue())

    def test_installer_uses_current_interpreter_and_checks_in_fresh_process(self):
        spec=importlib.util.spec_from_file_location('dependency_setup',ROOT/'setup-python.py')
        setup=importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)
        with patch.object(setup.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as run:
            self.assertEqual(setup.main(['--repair','--svg']),0)
        self.assertEqual(run.call_args_list[0].args[0][:4],[sys.executable,'-m','pip','install'])
        self.assertIn('--force-reinstall',run.call_args_list[0].args[0])
        self.assertIn('requirements.txt',run.call_args_list[0].args[0][5])
        self.assertIn('--check',run.call_args_list[1].args[0])


if __name__=='__main__': unittest.main()
