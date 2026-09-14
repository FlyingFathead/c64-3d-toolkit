"""The new cart baseline must cover the actual released SAKU key contract."""
import json
from pathlib import Path
import unittest
from tools.c643d.interactive_cart_baseline import collection_help_pages, describe_collection
from tools.c643d.hors_v3_help import packed_help

ROOT=Path(__file__).resolve().parents[1]


class InteractiveBaselineTests(unittest.TestCase):
    def test_complete_saku_command_contract(self):
        source=json.loads((ROOT/'examples/saku_2026/cartridges/saku_2026-interactive-manifest.json').read_text())
        collection=json.loads((ROOT/'examples/gmod3_cart_demos/demo-cart-v3.1-gmod3-all-in-one-manifest.json').read_text())
        current=collection['entries'][0]['runtime']
        self.assertEqual(set(source['interactive_cart']['keys'])-set(current['interactive_cart']['keys']),set())
        self.assertIn('menu',current['interactive_cart']['keys']['RUN/STOP (Esc in VICE)'])
        self.assertEqual(current['background_effect']['name'],'none')
        self.assertTrue(current['background_effect']['included'])

    def test_help_visible_controls_and_memory(self):
        for modes in (False,True):
            pages=collection_help_pages(modes=modes)
            self.assertEqual(len(pages),2)
            self.assertLessEqual(len(packed_help(pages)[0])+4,1024)
            self.assertTrue(all(len(p)<=25 and all(len(line)<=40 for line in p) for p in pages))
            for key in ('SHIFT+I','SHIFT+F','SHIFT+U','SHIFT+S','1/2/3','4 '):
                self.assertTrue(any(key in line for line in pages[0]),key)
            self.assertTrue(any('RIGHT:' in line for line in pages[0]))
            self.assertTrue(any('LEFT:' in line for line in pages[1]))
            for key in ('F3','F4','F5','F6/F7','F8','CTRL+F7','5 ','6 ','7/8'):
                self.assertTrue(any(key in line for line in pages[1]),key)
            if modes:
                for key in ('SHIFT+T/W','SHIFT+G','SHIFT+R','SHIFT+B','SHIFT+O'):
                    self.assertTrue(any(key in line for line in pages[1]),key)

if __name__=='__main__':unittest.main()
