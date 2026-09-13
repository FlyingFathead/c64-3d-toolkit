"""Release gates for the isolated comparison builder and intentional V9 defaults."""
import contextlib
import io
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import compare_renderers as comparison
from c643d import cli
from c643d.toolchain import load_toolchain_settings

class ComparisonTests(unittest.TestCase):
    def test_snapshot_adapter_accepts_current_verifier_and_keeps_border_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for rel in ('tools/c643d/cartuniform.py',
                        'c64/cart/easyflash-demo-scroll-runtime-v9.asm',
                        'c64/cart/easyflash-demo-control-v9.asm',
                        'tools/verify_cart_stream.py', 'tools/profile_cart_stream.py',
                        'tools/benchmark_play_all.py'):
                dest=root/rel;dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/rel,dest)
            comparison.adapt_snapshot(root)
            adapted=(root/'tools/verify_cart_stream.py').read_text()
            compile(adapted,'adapted_verifier','exec')
            self.assertIn('border colour mismatch',adapted)
            self.assertIn("result['display_interval_cycles']",adapted)

    def test_workspace_cannot_overwrite_project(self):
        run=subprocess.run([sys.executable,str(ROOT/'tools/compare_renderers.py'),
                            '--workspace',str(ROOT/'examples'),'--vice-data','/tmp'],capture_output=True,text=True)
        self.assertEqual(run.returncode,2)
        self.assertIn('workspace must be external',run.stderr)

    def test_pacing_options_are_exclusive(self):
        run=subprocess.run([sys.executable,str(ROOT/'tools/compare_renderers.py'),
                            '--max-fps','10','--lock-to-min-fps'],capture_output=True,text=True)
        self.assertEqual(run.returncode,2)
        self.assertIn('not allowed with argument',run.stderr)

    def test_fingerprint_tracks_inputs_not_local_config_or_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for folder in ('tools','c64','assets','config','examples'): (root/folder).mkdir()
            (root/'VERSION').write_text('0.6.9\n');(root/'.gitignore').write_text('/comparison-tests/\n')
            (root/'assets/input.json').write_text('original')
            for rel in (*comparison.SHOWCASE_REPORTS,comparison.SHOWCASE_CART,comparison.SANDE_REPORT,
                        'examples/demos_sande/recipe.json'):
                path=root/rel;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(b'original showcase evidence')
            before=comparison.fingerprints(root)[1]
            (root/'config/c643d.ini').write_text('local tool paths')
            (root/'examples/README.md').write_text('documentation')
            self.assertEqual(before,comparison.fingerprints(root)[1])
            # A README-linked recording must remain in assets without making
            # the renderer evidence stale, regardless of Git ignore rules.
            for suffix in ('.mp4','.MP4','.m4v','.mov','.webm','.mkv','.avi'):
                with self.subTest(video_suffix=suffix):
                    video=root/('assets/showreel'+suffix)
                    video.write_bytes(b'local video fixture')
                    self.assertEqual(before,comparison.fingerprints(root)[1])
                    video.write_bytes(b'updated video fixture')
                    self.assertEqual(before,comparison.fingerprints(root)[1])
                    video.unlink()
                    self.assertEqual(before,comparison.fingerprints(root)[1])
            (root/'assets/input.json').write_text('changed pictures')
            self.assertNotEqual(before,comparison.fingerprints(root)[1])
            before=comparison.fingerprints(root)[1]
            (root/comparison.SHOWCASE_REPORTS[0]).write_text('changed measurements')
            self.assertNotEqual(before,comparison.fingerprints(root)[1])

    def test_frozen_scene_references_are_self_contained(self):
        refs=comparison.load_scene_references(ROOT)
        self.assertEqual(set(refs),{'marbles','horse-sunflower'})
        for frames,scene,manifest in refs.values():
            self.assertEqual(len(frames),manifest['frames'])
            self.assertEqual([f.source_frame for f in scene.frames],manifest['source_frames'])
            self.assertTrue(all(f.records for f in frames))

    def test_frozen_scene_reference_rejects_changed_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'assets').mkdir()
            (root/'assets/comparison-scene-vector-reference.json.gz').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'frozen baseline'):
                comparison.load_scene_references(root)

    def test_scene_startup_wait_is_acknowledged_only_when_required(self):
        from verify_cart_stream import startup_monitor
        self.assertEqual(startup_monitor({},{}),([], 'g'))
        self.assertEqual(startup_monitor({'build_screen':{'wait_for_space':False}},{}),([], 'g'))
        commands,go=startup_monitor({'build_screen':{'wait_for_space':True}},
                                   {'build_screen_visible':0x8123,'build_screen_done':0x8156})
        self.assertEqual(commands,['break $8123','g','delete'])
        self.assertEqual(go,'g $8156')
        with self.assertRaises(KeyError):
            startup_monitor({'build_screen':{'wait_for_space':True}}, {})

    def test_cart_stream_default_and_explicit_old_method(self):
        with patch.object(cli,'cmd_build',return_value=0) as build,contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['cart-stream','--no-config']),0)
            self.assertEqual(build.call_args.args[0].renderer,'hors-renderer-v3')
            self.assertEqual(cli.main(['cart-stream','--no-config','--renderer','yunroll-cart-v2']),0)
            self.assertEqual(build.call_args.args[0].renderer,'yunroll-cart-v2')

    def test_default_authored_input_selects_v9_scene(self):
        parser=cli.make_parser(load_toolchain_settings(Path('/missing/config.ini')))
        args=parser.parse_args(['build','--scene','example.c643dscene'])
        with patch('c643d.cartscene.cmd_build_cart_scene',return_value=0) as build,contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.cmd_build(args),0)
            self.assertEqual(build.call_args.args[0].renderer,'yunroll-cart-v10-scene')

if __name__=='__main__':unittest.main()
