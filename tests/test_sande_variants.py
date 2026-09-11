"""The bw default and explicit source-material variant must stay separate."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_sande_examples as sande


class BeforeCompile(Exception):
    pass


class SandeVariantTests(unittest.TestCase):
    def arguments(self, **options):
        with tempfile.TemporaryDirectory() as tmp, patch.object(sande.cli, 'main', side_effect=BeforeCompile) as compile_cart:
            with self.assertRaises(BeforeCompile):
                sande.build(tmp, models=('sande_tac2',), **options)
            return compile_cart.call_args.args[0]

    def test_default_stays_bw_and_color_uses_mtl(self):
        bw = self.arguments()
        color = self.arguments(source_colors=True)
        self.assertIn('--no-color', bw)
        self.assertEqual(bw[bw.index('--color') + 1], 'white')
        self.assertNotIn('--no-color', color)
        self.assertNotIn('--color', color)
        self.assertEqual(bw[bw.index('--output') + 1], 'sande_tac2-hors-render-v2')
        self.assertEqual(color[color.index('--output') + 1], 'sande_tac2-hors-render-v2-color')
        for flag in ('--obj', '--frames', '--spin-axis', '--visibility', '--background-color', '--border-color'):
            self.assertEqual(bw[bw.index(flag) + 1], color[color.index(flag) + 1])

    def test_source_materials_cannot_be_silently_forced_to_interactive_bw(self):
        with patch.object(sande.cli, 'main') as compile_cart:
            with self.assertRaisesRegex(ValueError, 'separate variants'):
                sande.build(interactive=True, source_colors=True)
            compile_cart.assert_not_called()


if __name__ == '__main__':
    unittest.main()
