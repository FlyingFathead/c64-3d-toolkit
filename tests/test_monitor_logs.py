"""Check preservation of monitor output and cleanup of real Git index entries."""
import contextlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tools.c643d import monitor_logs


class MonitorLogTests(unittest.TestCase):
    def test_copy_is_verified_timestamped_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root/'monitor.log'
            source.write_bytes(b'first\x00trace\n')
            first = monitor_logs.archive_root_monitor(root)
            self.assertFalse(source.exists())
            self.assertEqual(first.read_bytes(), b'first\x00trace\n')
            self.assertRegex(first.name, r'^monitor-\d{8}T\d{6}\.\d{6}Z-.+\.log$')
            source.write_bytes(b'second trace')
            second = monitor_logs.archive_root_monitor(root)
            self.assertNotEqual(first, second)
            self.assertEqual(first.read_bytes(), b'first\x00trace\n')
            self.assertEqual(second.read_bytes(), b'second trace')
            self.assertIsNone(monitor_logs.archive_root_monitor(root))
            self.assertEqual(len(list((root/'logs').iterdir())), 2)

    def test_unwritable_destination_preserves_original(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'monitor.log').write_bytes(b'preserve me')
            (root/'logs').write_text('not a directory')
            with self.assertRaises(OSError):
                monitor_logs.archive_root_monitor(root)
            self.assertEqual((root/'monitor.log').read_bytes(), b'preserve me')

    def test_failed_copy_verification_preserves_original(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'monitor.log').write_bytes(b'preserve me')
            with mock.patch.object(monitor_logs, '_digest', side_effect=[b'a', b'b']):
                with self.assertRaisesRegex(OSError, 'original retained'):
                    monitor_logs.archive_root_monitor(root)
            self.assertEqual((root/'monitor.log').read_bytes(), b'preserve me')

    def test_missing_log_is_a_noop(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertIsNone(monitor_logs.archive_root_monitor(root))
            self.assertFalse((root/'logs').exists())

    def test_default_vice_logs_are_unique_and_ignored_locations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = monitor_logs.vice_monitor_args(['-default', '-monlog'], root=root)
            second = monitor_logs.vice_monitor_args(['-default', '-monlog'], root=root)
            self.assertLess(first.index('-monlogname'), first.index('-monlog'))
            self.assertEqual(Path(first[1]).parent, root/'logs')
            self.assertNotEqual(first[1], second[1])
            self.assertTrue(Path(first[1]).is_file())
            self.assertFalse((root/'monitor.log').exists())

    def test_explicit_diagnostic_log_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            args = ["-monlog", "-monlogname", str(root/"diagnostic.log")]
            result = monitor_logs.vice_monitor_args(args, root=root)
            self.assertEqual(result[:2], ['-monlogname', str(root/'diagnostic.log')])
            self.assertIn('-monlog', result)
            self.assertFalse((root/'logs').exists())

    def test_cli_startup_archives_before_dispatch(self):
        from tools.c643d import cli
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'monitor.log').write_bytes(b'stale startup log')
            def dispatch(argv):
                self.assertFalse((root/'monitor.log').exists())
                return 17
            with mock.patch.object(cli, 'ROOT', root), mock.patch.object(cli, '_main', side_effect=dispatch):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(cli.main(['--version']), 17)
            self.assertEqual(next((root/'logs').iterdir()).read_bytes(), b'stale startup log')

    @unittest.skipUnless(shutil.which('git'), 'Git required for index maintenance check')
    def test_maintenance_preserves_local_and_staged_logs_and_untracks_only_logs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.STDOUT)
            git('init', '-q')
            names = ['monitor.log', 'docs/benchmarks/example/monitor.log']
            for name in names:
                path = root/name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'committed '+name.encode())
            (root/'.gitignore').write_text('logs/\n*.log\n')
            git('add', '--force', '.gitignore', *names)
            git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'baseline')
            for name in names:
                (root/name).write_bytes(b'staged '+name.encode())
            git('add', '--force', *names)
            for name in names:
                (root/name).write_bytes(b'working '+name.encode())
            (root/'unrelated.txt').write_text('keep staged')
            git('add', 'unrelated.txt')
            command = [sys.executable, str(Path(__file__).resolve().parents[1]/'tools/maintenance.py'),
                       '--root', str(root), '--untrack-monitor-logs']
            subprocess.run(command, check=True, capture_output=True)
            self.assertNotIn(b'monitor.log', git('ls-files'))
            self.assertIn(b'A\tunrelated.txt', git('diff', '--cached', '--name-status'))
            contents = {p.read_bytes() for p in (root/'logs').iterdir()}
            for name in names:
                self.assertFalse((root/name).exists())
                self.assertIn(b'working '+name.encode(), contents)
                self.assertIn(b'staged '+name.encode(), contents)
            before = set((root/'logs').iterdir())
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual(set((root/'logs').iterdir()), before)
