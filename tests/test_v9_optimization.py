"""V9 directory flags, preserved V8 payloads and frozen historical releases."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.c643d.cartscene import pack_scene_frames
from tools.c643d.cartstream import emit_directory
from tools.c643d.cartridge import easyflash_offset
from tools.c643d.bytespan import frame_block
from tools.c643d.pipeline import FrameBuild
from tools.c643d.cli import make_parser
from tools.c643d.toolchain import load_toolchain_settings
from tools.c643d.cartuniform import play_all_durations


class V9Tests(unittest.TestCase):
    def test_every_pre_v9_renderer_and_executable_is_frozen(self):
        root=Path(__file__).resolve().parents[1]
        frozen=json.loads((root/'tests/data/preserved-v0.6.8.json').read_text())
        for name,digest in frozen['files'].items():
            if name.startswith('../'): continue  # Checked separately when the external archive is available.
            self.assertEqual(hashlib.sha256((root/('build/reference-prgs/'+name if name.startswith('examples/') and name.endswith('.prg') else name)).read_bytes()).hexdigest(),digest,name)

    def test_external_historical_binaries(self):
        import hashlib, json
        root=Path(__file__).resolve().parents[1]
        frozen=json.loads((root/'tests/data/preserved-v0.6.8.json').read_text())
        external={k:v for k,v in frozen['files'].items() if k.startswith('../')}
        if not (root.parent/'c64-3d-toolkit-history').exists():
            self.skipTest('Optional historical archive is outside the checkout and not installed')
        missing = []
        for name, expected in external.items():
            if not (root/name).is_file():
                missing.append(name)
                continue
            self.assertEqual(hashlib.sha256((root/('build/reference-prgs/'+name if name.startswith('examples/') and name.endswith('.prg') else name)).read_bytes()).hexdigest(),expected,name)
        if missing:
            self.skipTest(f'Optional historical archive is incomplete: {len(missing)} reference files absent')

    def test_directory_flag_does_not_change_payloads_or_aliases(self):
        from tools.c643d.pipeline import encode_run,oriented_dda
        # Multiple short runs make literal bytes win. Empty pictures stay vectors.
        rec=[encode_run(oriented_dda(0,y,1,y),0,1) for y in range(8)]
        byte=FrameBuild(rec,[(0,0,1)],16,16,[],[(0,0,1,16)])
        empty=FrameBuild([],[],0,0,[],[])
        frames=[byte,empty,byte]*90;aliases=[i if i<2 else i%3 if i%3<2 else 0 for i in range(len(frames))]
        legacy,d8=pack_scene_frames(frames,encoder=frame_block,aliases=aliases)
        direct,d9=pack_scene_frames(frames,encoder=frame_block,aliases=aliases,direct_bytes=True)
        self.assertEqual(d8,d9)
        self.assertEqual({d['encoding'] for d in d9},{'vectors','byte-spans'})
        allowed=set()
        for page in range(2):
            start=easyflash_offset(1,'romh',page*1792)+4*256
            for i,d in enumerate(d9[page*256:(page+1)*256]):
                if d['encoding']=='byte-spans':allowed.add(start+i)
        differing={i for i,(a,b) in enumerate(zip(legacy,direct)) if a!=b}
        self.assertEqual(differing,allowed)
        for i in differing:self.assertEqual(direct[i],legacy[i]|128)

    def test_small_directory_opt_in_and_old_default(self):
        data=[dict(bank=3,address=0x8100,bytes=100,metadata_bytes=9,encoding='byte-spans'),
              dict(bank=3,address=0x8200,bytes=250,metadata_bytes=9,encoding='vectors')]
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/'old.inc';b=Path(td)/'new.inc';emit_directory(a,data);emit_directory(b,data,direct_bytes=True)
            old=a.read_text();new=b.read_text()
            self.assertNotEqual(old,new)
            self.assertEqual(old.split('cart_length_hi:')[0],new.split('cart_length_hi:')[0])
            self.assertEqual(old.split('cart_meta_lo:')[1],new.split('cart_meta_lo:')[1])

    def test_v9_is_opt_in_and_exhibition_remains_separate(self):
        p=make_parser(load_toolchain_settings(Path('/missing/config.ini')))
        self.assertEqual(p.parse_args(['cart-demos']).stream_renderer,'hors-render-v2')
        self.assertEqual(p.parse_args(['build']).renderer,'hors-renderer-v3')
        for variant in ('yunroll-cart-v9','yunroll-cart-v9-scene'):
            self.assertEqual(p.parse_args(['build','--renderer',variant]).renderer,variant)
        self.assertEqual(p.parse_args(['cart-demos','--stream-renderer','yunroll-cart-v9']).play_all_seconds,10)
        entries=[{'name':s} for s in ['CUBE','HORSE HEAD HIFI','SUNFLOWER TORUS HIFI']]
        self.assertEqual(play_all_durations(entries,10,'yunroll-cart-v9'),[10,15,15])
        self.assertEqual(play_all_durations(entries,20,'yunroll-cart-v9'),[20]*3)
