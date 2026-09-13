"""Exhibition interface, page dimensions and packed text round trip."""
import unittest
from tools.c643d import cli
from tools.c643d.toolchain import ToolchainSettings
from tools.c643d.hors_v3_help import help_pages,packed_help
from tools.c643d.buildscreen import screen_codes
from tools.c643d.hors_v3_exhibition import loops

class ExhibitionTests(unittest.TestCase):
    def test_pages_fit_and_decompress(self):
        for stars in (False,True):
            for hud in (False,True):
                pages=help_pages('0.7.9',effects=stars,hud=hud,modes=True,variants=('card','outline'))
                data,offsets=packed_help(pages)
                self.assertLessEqual(len(data)+4,1024)
                for page,start in zip(pages,offsets):
                    i=start;actual=[]
                    while data[i]!=255:
                        width=data[i];i+=1;line=[]
                        while len(line)<width:
                            c=data[i];i+=1
                            if c==254:line.extend([32]*data[i]);i+=1
                            else:line.append(c)
                        actual.append(line)
                    self.assertEqual(actual,[screen_codes(line) for line in page])
                    self.assertLessEqual(len(page),25)
                    self.assertTrue(all(len(line)<=40 for line in page))
    def test_loop_metadata_uses_only_compiled_styles(self):
        self.assertEqual(loops(30,('card','outline')),[('solid outline',6,7),('gradient',1,3),('white card',4,5)])
        self.assertEqual(len(loops(30,())),2)
        self.assertEqual(loops(0,()),[('current loop',0,0)])
    def test_cli_defaults_and_opt_in(self):
        p=cli.make_parser(ToolchainSettings())
        a=p.parse_args(['build','--interactive-cart'])
        self.assertIsNone(a.exhibition_default)
        self.assertIsNone(a.starfield_default)
        a=p.parse_args(['build','--interactive-cart','--exhibition-default','enabled','--exhibition-order','random','--exhibition-interval','60'])
        self.assertEqual((a.exhibition_default,a.exhibition_order,a.exhibition_interval),('enabled','random',60))
        with self.assertRaisesRegex(ValueError,'Exhibition options require'):
            cli.cmd_build(p.parse_args(['build','--exhibition-default','enabled']))
