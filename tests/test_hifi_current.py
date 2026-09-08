import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from perf import prune_old_examples


class CurrentHiFiTests(unittest.TestCase):
    def test_prune_keeps_current_hifi_and_removes_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'repo'
            root.mkdir()
            (root / 'VERSION').write_text('0.7.0\n')
            names = ['examples/cart_marbles/marbles-hors-render-v1-16fps-force-bytes.crt',
                     'examples/hifi_showcase/README.md']
            names += ['examples/hifi_showcase/horse_head_hifi-hors-render-v1' + suffix
                      for suffix in ('.crt', '.lbl', '-manifest.json')]
            old = root / 'examples/hifi_showcase/horse_head_hifi-yunroll-cart-v3.crt'
            for name in names + [str(old.relative_to(root))]:
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b'example')
            with patch.object(prune_old_examples, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                prune_old_examples.main()
                prune_old_examples.main()
            for name in names:
                self.assertEqual((root / name).read_bytes(), b'example')
            self.assertFalse(old.exists())
