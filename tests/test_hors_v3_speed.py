import unittest
from tools.c643d.hors_v3_speed import levels
from tools.c643d.hors_v3_effects import trajectories

class TempoAndStars(unittest.TestCase):
    def test_fast_steps_never_reach_half_turn_or_full_turn_alias(self):
        for samples in (1,2,3,4,48,128,255):
            rates=levels(samples)
            self.assertEqual(rates[:4],[(1,8),(1,4),(1,2),(1,1)])
            skips=[n for n,d in rates[3:]]
            self.assertEqual(skips,sorted(set(skips)))
            self.assertEqual(skips[-1],max(1,(samples-1)//2))
            if samples>2:self.assertTrue(all(0<n<samples/2 for n in skips))

    def test_star_paths_accelerate_outward_inside_the_viewport(self):
        for points in trajectories():
            radii=[(x-128)**2+(y-96)**2 for x,y in points]
            self.assertEqual(len(points),64)
            self.assertTrue(all(0<=x<256 and 0<=y<192 for x,y in points))
            self.assertEqual(radii,sorted(radii))
            self.assertGreater(radii[-1]-radii[-5],radii[5]-radii[0])
