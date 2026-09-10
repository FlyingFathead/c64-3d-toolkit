import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from tools.c643d.hors_v2 import encoder as beta_encoder
from tools.c643d.hors_v2_stable import encoder
from tools.c643d.pipeline import FrameBuild
from tools.c643d.cartframes import load_menu_reference
from tools.c643d.cartstream import frame_block
from tools.c643d.cli import make_parser
from tools.c643d.toolchain import load_toolchain_settings
from tools.cleanup_examples import cleanup

ROOT=Path(__file__).resolve().parents[1]


class StableV2Tests(unittest.TestCase):
    def test_version_is_loaded_from_a_different_checkout(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);pkg=root/'tools/c643d';pkg.mkdir(parents=True)
            for name in ('__init__.py','versioning.py'):
                (pkg/name).write_bytes((ROOT/'tools/c643d'/name).read_bytes())
            (root/'VERSION').write_text('9.8.7\n')
            result=subprocess.check_output([sys.executable,'-c',
                "import sys;sys.path.insert(0,'tools');import c643d;print(c643d.__version__)"],cwd=root,text=True)
            self.assertEqual(result.strip(),'9.8.7')

    def test_alternate_version_reaches_all_generated_title_text(self):
        from tools.c643d.versioning import stamp_menu_source
        from tools.c643d.buildscreen import build_screen_lines,menu_title_lines,play_all_thanks_lines,screen_codes
        from tools.c643d.emit import bytes_lines
        for name in ('easyflash-demo-scroll-runtime.asm','easyflash-demo-scroll-runtime-v8.asm',
                     'easyflash-demo-scroll-runtime-v9.asm','easyflash-demo-scroll-runtime-v10.asm','easyflash-hifi-reel-runtime.asm'):
            original=(ROOT/'c64/cart'/name).read_text()
            changed=stamp_menu_source(original,'9.8.7')
            self.assertIn('TOOLKIT 9.8.7',changed)
            self.assertNotEqual(original,changed)
        expected='\n'.join(bytes_lines(screen_codes('v. 9.8.7')))
        self.assertIn(expected,'\n'.join(build_screen_lines('9.8.7','hors-render-v1')))
        for lines,text in ((menu_title_lines('9.8.7','hors-render-v1'),'C64 3D TOOLKIT 9.8.7 HORS-V1'),
                           (play_all_thanks_lines('9.8.7'),'c64-3d-toolkit v9.8.7')):
            self.assertIn('\n'.join(bytes_lines(screen_codes(text))),'\n'.join(lines))

    def test_beta_supported_wire_bytes_are_unchanged(self):
        for demo in load_menu_reference(ROOT):
            for frame in demo.frames[:2]:
                for gap,budget in ((3,1024),(6,2048),(10,2048)):
                    try: expected=beta_encoder(gap,budget)(frame,demo.colors)
                    except ValueError: continue
                    self.assertEqual(encoder(gap,budget)(frame,demo.colors),expected)

    def test_large_unused_vector_does_not_reject_small_literal_picture(self):
        # Duplicate input records exceed vector staging but paint one tiny picture.
        frame=FrameBuild([(0,0,2,0,0)]*2000,[(0,0,1)],4000,2,[],[])
        with self.assertRaisesRegex(ValueError,'staging buffer'):frame_block(frame,False)
        block,meta=encoder()(frame,False)
        self.assertLess(len(block),32)
        self.assertTrue(block[meta+1]&128)

    def test_metadata_limit_still_rejects(self):
        frame=FrameBuild([],[(0,0,1)]*255,0,0,[],[(0,0,1,16)]*255)
        with self.assertRaisesRegex(ValueError,'1 KiB'):encoder()(frame)

    def test_defaults_and_old_names(self):
        parser=make_parser(load_toolchain_settings(Path('/missing/config.ini')))
        self.assertEqual(parser.parse_args(['build']).renderer,'hors-render-v2')
        self.assertEqual(parser.parse_args(['cart-demos']).stream_renderer,'hors-render-v2')
        for name in ('hors-render-v1','yunroll-cart-v9','hors-render-v2-beta1'):
            self.assertEqual(parser.parse_args(['build','--renderer',name]).renderer,name)

    def test_cleanup_checks_every_replacement_before_moving(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'repo';(root/'examples').mkdir(parents=True);(root/'assets').mkdir()
            old=root/'examples/old.crt';old.write_bytes(b'local old')
            (root/'assets/legacy-example-files.json').write_text(json.dumps(['examples/old.crt']))
            (root/'examples/release-index.json').write_text(json.dumps({'files':[{'path':'examples/new.crt','sha256':'missing'}]}))
            with self.assertRaisesRegex(ValueError,'Replacement missing'):cleanup(root,apply=True)
            self.assertEqual(old.read_bytes(),b'local old')

    def test_cleanup_preserves_local_changes_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as td,contextlib.redirect_stdout(io.StringIO()):
            root=Path(td)/'repo';(root/'examples').mkdir(parents=True);(root/'assets').mkdir()
            archive=Path(td)/'archive';(archive/'examples').mkdir(parents=True)
            (root/'examples/old.crt').write_bytes(b'local edit');(archive/'examples/old.crt').write_bytes(b'previous')
            new=root/'examples/new.crt';new.write_bytes(b'new')
            (root/'assets/legacy-example-files.json').write_text(json.dumps(['examples/old.crt']))
            (root/'examples/release-index.json').write_text(json.dumps({'files':[{'path':'examples/new.crt','sha256':hashlib.sha256(b'new').hexdigest()}]}))
            self.assertEqual(cleanup(root,archive=archive,apply=True),1)
            self.assertEqual((archive/'examples/old.crt').read_bytes(),b'previous')
            self.assertEqual(next((archive/'local-modified').rglob('old.crt')).read_bytes(),b'local edit')
            self.assertEqual(cleanup(root,archive=archive,apply=True),0)


if __name__=='__main__':unittest.main()
