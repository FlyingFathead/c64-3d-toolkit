from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from compare_cart_stream import require_matched


class ComparisonGuards(unittest.TestCase):
    def test_picture_order_or_colour_mismatch_rejected(self):
        a = dict(pictures_sha256='same-pictures', meta=dict(frames=120))
        b = deepcopy(a)
        b['pictures_sha256'] = 'different-pictures'
        with self.assertRaisesRegex(ValueError, 'picture bytes, colours or sample order'):
            require_matched(a, b)

    def test_pacing_and_hud_must_match_even_with_same_pictures(self):
        a = dict(pictures_sha256='same-pictures', meta=dict(frames=120, frame_ticks=4, hud_text='SCENE'))
        require_matched(a, deepcopy(a))
        for field in ('frames', 'frame_ticks', 'hud_text', 'background_effect'):
            b = deepcopy(a)
            b['meta'][field] = 'different'
            with self.assertRaisesRegex(ValueError, field):
                require_matched(a, b)
