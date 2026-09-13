"""Reject unsupported interactive outputs before any build/toolchain work."""
import contextlib
import io
import unittest
from unittest.mock import patch

from tools.c643d import cli
from tools.c643d.toolchain import ToolchainSettings


class InteractiveCartTests(unittest.TestCase):
    def args(self, *extra):
        return cli.make_parser(ToolchainSettings()).parse_args(['build', '--interactive-cart', *extra])

    def test_rejects_prg_legacy_renderers_and_scenes_before_build(self):
        for extra in (('--renderer', 'yunroll'), ('--renderer', 'step'),
                      ('--renderer', 'hors-render-v1'), ('--renderer', 'yunroll-cart-v9'),
                      ('--scene', 'animation.c643dscene'), ('--blend', 'animation.blend'),
                      ('--output', 'output.prg'), ('--animation', 'crawl')):
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError, '--interactive-cart'):
                cli.cmd_build(self.args(*extra))

    def test_crt_extension_normalized_and_private_runtime_enabled(self):
        from tools.c643d import hors_v2_stable, sande_controls
        a = self.args('--renderer', 'hors-render-v2', '--output', 'demo.crt', '--border-color', 'blue')
        with contextlib.redirect_stdout(io.StringIO()), \
             patch.object(sande_controls, 'enabled') as enabled, \
             patch.object(hors_v2_stable, 'cmd_build_object', return_value=0) as build:
            self.assertEqual(cli.cmd_build(a), 0)
        enabled.assert_called_once_with(border=6, text_overlay=True)
        self.assertEqual(a.output, 'demo')
        self.assertTrue(a.ignore_colors)
        build.assert_called_once_with(a)


if __name__ == '__main__':
    unittest.main()
