import subprocess
import sys
import unittest
from pathlib import Path
from tools.c643d.cli import make_parser
from tools.c643d.toolchain import load_toolchain_settings

ROOT = Path(__file__).resolve().parents[1]


class HelpTests(unittest.TestCase):
    def test_root_help_contains_every_build_option_without_dependencies(self):
        result = subprocess.run([sys.executable, '-S', 'c643d.py', '--help'], cwd=ROOT,
                                text=True, capture_output=True)
        assert result.returncode == 0 and not result.stderr
        parser = make_parser(load_toolchain_settings(None))
        for action in parser.build_help_parser._actions:
            for flag in action.option_strings:
                assert flag in result.stdout, flag
        assert 'HORS-V4 / GMod3' in result.stdout
        assert 'non-interactive automatic playback' in ' '.join(result.stdout.split())
        assert '==SUPPRESS==' not in result.stdout
        assert 'HORS-V3 CRT by default' not in result.stdout
    
    
    def test_full_help_includes_other_commands(self):
        result = subprocess.run([sys.executable, '-S', 'c643d.py', '--help-all'], cwd=ROOT,
                                text=True, capture_output=True)
        assert result.returncode == 0 and not result.stderr
        for command in ('build', 'inspect', 'import-obj', 'import-svg', 'doctor', 'dependencies', 'run-cart'):
            assert 'usage: c643d ' + command in result.stdout
        assert '--starfield-default' in result.stdout and '--viewport-width' in result.stdout
