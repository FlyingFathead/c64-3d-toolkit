"""SVG paint, independent stroke colour, alpha geometry and CLI overrides."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from tools.c643d.svg_surface import bake_svg, surface_from_rgba, mask_rectangles
from tools.c643d.colors import nearest_c64_color_index
from tools.c643d import cli
from tools.c643d.toolchain import ToolchainSettings

try:
    import cairosvg
    HAVE_CAIRO = True
except (ImportError, OSError):
    HAVE_CAIRO = False


class MaskTests(unittest.TestCase):
    def test_holes_are_empty_and_rectangle_coverage_is_exact(self):
        mask=np.ones((12,15),dtype=bool);mask[3:8,4:10]=False;mask[8:,9:]=False
        counts=np.zeros_like(mask,dtype=int)
        for x0,y0,x1,y1 in mask_rectangles(mask): counts[y0:y1,x0:x1]+=1
        np.testing.assert_array_equal(counts,mask.astype(int))
        rgba=np.zeros((12,15,4),dtype=np.uint8);rgba[mask]=[0,0,0,255]
        result=surface_from_rgba(rgba,'hole',depth=3)
        self.assertEqual(result.report['opaque_texels'],int(mask.sum()))
        self.assertEqual(result.report['mapped_colors'][0]['c64_index'],0)
        self.assertGreater(result.report['wall_quads'],4)
        replacement=surface_from_rgba(rgba,'hole',depth=3,override_color=7)
        self.assertEqual(result.mesh.vertices,replacement.mesh.vertices)
        self.assertEqual(result.mesh.faces,replacement.mesh.faces)
        self.assertEqual(replacement.report['mapped_colors'],[dict(c64_index=7,c64_color='yellow',texels=int(mask.sum()))])


@unittest.skipUnless(HAVE_CAIRO,'optional CairoSVG host dependencies')
class PaintTests(unittest.TestCase):
    def bake(self,body,**kwargs):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'logo.svg'
            p.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'+body+'</svg>')
            return bake_svg(p,resolution=64,**kwargs)

    def test_fill_and_stroke_have_independent_nearest_colours(self):
        rgba,_=self.bake('<style>rect {fill:#fe0000;stroke:#0000ff;stroke-width:4}</style><rect x="8" y="8" width="48" height="48"/>')
        surface=surface_from_rgba(rgba,'paint')
        mapped={r['c64_index'] for r in surface.report['mapped_colors']}
        self.assertIn(nearest_c64_color_index((254,0,0)),mapped)
        self.assertIn(nearest_c64_color_index((0,0,255)),mapped)
        self.assertEqual(tuple(rgba[30,30]),(254,0,0,255))
        self.assertEqual(tuple(rgba[8,30]),(0,0,255,255))

    def test_outlines_ignore_fill_but_keep_inherited_stroke_and_holes(self):
        rgba,_=self.bake('<g style="stroke:blue;stroke-width:4;fill:red"><path d="M8 8H56V56H8Z M24 24H40V40H24Z" fill-rule="evenodd"/></g>',outlines_only=True)
        self.assertEqual(int(rgba[16,16,3]),0)
        self.assertEqual(int(rgba[32,32,3]),0)
        self.assertEqual(tuple(rgba[8,30]),(0,0,255,255))
        self.assertEqual(tuple(rgba[24,30]),(0,0,255,255))

    def test_fill_only_outline_is_white_and_original_gradient_survives_normally(self):
        body='<defs><linearGradient id="g"><stop stop-color="red"/><stop offset="1" stop-color="blue"/></linearGradient></defs><rect x="8" y="8" width="48" height="48" fill="url(#g)"/>'
        rgba,_=self.bake(body)
        self.assertGreater(int(rgba[30,12,0]),int(rgba[30,12,2]))
        self.assertGreater(int(rgba[30,52,2]),int(rgba[30,52,0]))
        outlines,_=self.bake(body,outlines_only=True)
        self.assertEqual(int(outlines[30,30,3]),0)
        self.assertTrue(np.all(outlines[8,30,:3]==255))

    def test_reused_shape_keeps_each_instances_stroke(self):
        rgba,_=self.bake('<defs><rect id="box" x="0" y="0" width="16" height="16" fill="red"/></defs><use href="#box" x="8" y="8" stroke="blue" stroke-width="4"/><use href="#box" x="36" y="36" stroke="lime" stroke-width="4"/>',outlines_only=True)
        self.assertEqual(tuple(rgba[8,16]),(0,0,255,255))
        self.assertEqual(tuple(rgba[36,44]),(0,255,0,255))
        self.assertEqual(int(rgba[16,16,3]),0)

    def test_canvas_paint_is_preserved_unless_explicitly_removed(self):
        for dimension in ('64','100%'):
            body=f'<rect width="{dimension}" height="{dimension}" fill="white"/><circle cx="32" cy="32" r="12" fill="red"/>'
            normal,_=self.bake(body);cropped,report=self.bake(body,keep_background=False)
            self.assertEqual(int(normal[0,0,3]),255)
            self.assertEqual(int(cropped[0,0,3]),0)
            self.assertEqual(report['background_rectangles_removed'],1)


class SwitchTests(unittest.TestCase):
    def args(self,*args):
        return cli.make_parser(ToolchainSettings()).parse_args(['build','--svg','example.svg',*args])

    def selected(self,*args):
        a=self.args(*args)
        with patch('tools.c643d.hors_v3.cmd_build',return_value=0): cli.cmd_build(a)
        return a

    def test_defaults_and_aliases(self):
        self.assertEqual(self.selected().surface_fill,'material')
        self.assertTrue(self.selected().svg_keep_background)
        for value in ('true','yes','on','1'):
            self.assertTrue(self.selected('--include-svg-background-color',value).svg_keep_background)
        for value in ('false','no','off','0'):
            self.assertFalse(self.selected('--include-svg-background-color',value).svg_keep_background)
        for flag in ('--svg-no-colors','--no-svg-color-mapping'):
            a=self.selected(flag)
            self.assertEqual((a.surface_fill,a.color,a.background_color),('material','white','black'))
        for flag in ('--svg-override-with-color','--override-svg-color'):
            a=self.selected(flag,'yellow')
            self.assertEqual(a.svg_override_with_color,'yellow')
            self.assertEqual(a.surface_fill,'material')
        self.assertEqual(self.selected('--svg-override-with-color','red','--fill-style','gradient').surface_fill,'gradient')

    def test_hud_startup_and_switch_inclusion(self):
        a=self.selected('--interactive-cart')
        self.assertTrue(a.hud_visible);self.assertTrue(a.hud_toggle_allowed)
        for flag in ('--hide-hud','--no-text-overlay'):
            self.assertFalse(self.selected(flag).hud_visible)
        for flag in ('--hud-default','--default-info-text-mode'):
            self.assertFalse(self.selected(flag,'disabled').hud_visible)
            self.assertTrue(self.selected('--hide-hud',flag,'enabled').hud_visible)
        self.assertFalse(self.selected('--interactive-cart','--no-hud-toggle').hud_toggle_allowed)
        with self.assertRaises(ValueError):self.selected('--allow-hud-toggle')

    def test_conflicts_are_explicit(self):
        for flags in [('--svg-no-colors','--svg-override-with-color','red'),
                      ('--svg-outlines-only','--fill-style','wireframe'),
                      ('--svg-no-colors','--background-effect','starfield'),
                      ('--svg-background-card','card.svg'),
                      ('--svg-outline-variant','outline.svg'),
                      ('--svg-presentation-modes',)]:
            with self.assertRaises(ValueError): self.selected(*flags)

    def test_starfield_inclusion_and_initial_state_are_separate(self):
        default=self.selected('--interactive-cart')
        self.assertTrue(default.include_starfield)
        self.assertEqual(default.background_effect,'none')
        for enabled in ('enabled','true'):
            self.assertEqual(self.selected('--starfield-default',enabled).background_effect,'starfield-forward')
        for disabled in ('disabled','false'):
            self.assertEqual(self.selected('--background-effect','starfield','--starfield-default',disabled).background_effect,'none')
        for flag in ('--no-starfield','--no-include-starfield'):
            self.assertFalse(self.selected(flag).include_starfield)
            with self.assertRaises(ValueError): self.selected(flag,'--starfield-default','enabled')

    def test_starfield_profile_is_independent_and_requires_interactive_stars(self):
        self.assertIsNone(self.selected('--interactive-cart').starfield_profile)
        for profile in ('light','full'):
            a=self.selected('--interactive-cart','--starfield-profile',profile)
            self.assertEqual(a.starfield_profile,profile)
            self.assertEqual(a.background_effect,'none')
            a=self.selected('--interactive-cart','--starfield-profile',profile,'--starfield-default','enabled')
            self.assertEqual(a.background_effect,'starfield-forward')
            with self.assertRaises(ValueError):self.selected('--starfield-profile',profile)
            with self.assertRaises(ValueError):self.selected('--interactive-cart','--starfield-profile',profile,'--no-starfield')
