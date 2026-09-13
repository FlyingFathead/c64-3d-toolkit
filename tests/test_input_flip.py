"""Exact artwork reflection, including native DDA ties and cell colours."""
import unittest
from pathlib import Path
import numpy as np
from tools.c643d import cli, input_flip
from tools.c643d.toolchain import ToolchainSettings
from tools.c643d.mesh import Mesh
from tools.c643d.pipeline import (Camera, FrameBuild, build_frames,
    build_scene_frames, decode_record_points, encode_run, oriented_dda)
from tools.c643d.sceneio import Projection, SceneAnimation, SceneFrame
from tools.c643d.surface_fill import build_frames as filled_frames
from tools.c643d.optimize import picture_bytes


def pixels(frame):
    return {p for rec in frame.records for p in decode_record_points(rec)}


def cells(spans):
    return {i:color for lo,hi,count,color in spans
            for i in range(lo+(hi<<8),lo+(hi<<8)+count)}


def clear_cells(frame):
    return {i for lo,hi,count in frame.clear_spans
            for i in range((lo+(hi<<8))//8,(lo+(hi<<8))//8+count)}


class InputFlipTests(unittest.TestCase):
    def test_all_aliases_are_opt_in_and_idempotent(self):
        parser=cli.make_parser(ToolchainSettings())
        self.assertEqual(input_flip.options(parser.parse_args(['build'])),
                         dict(flip_horizontal=False,flip_vertical=False))
        for direction in ('horizontal','vertical'):
            aliases=['--'+prefix+direction for prefix in ('flip-input-','flip-','mirror-')]
            for flags in [[name] for name in aliases]+[aliases]:
                for command in ('build',):
                    args=parser.parse_args([command,*flags])
                    self.assertEqual(input_flip.options(args),
                        dict(flip_horizontal=direction=='horizontal',flip_vertical=direction=='vertical'))
        args=parser.parse_args(['build','--mirror-horizontal','--flip-input-vertical'])
        self.assertTrue(all(input_flip.options(args).values()))

    def test_native_records_reflect_exact_pixels_at_boundaries(self):
        # Both axes/directions, nontrivial DDA ties, count=127 and cell edges.
        for height in (144,192,200):
            lines=[(0,0,126,19),(129,8,255,8),(31,0,11,126),
                   (255,height-1,239,height-127),(128,51,44,126),(7,7,8,8)]
            recs=[encode_run(oriented_dda(*line),0,max(abs(line[2]-line[0]),abs(line[3]-line[1]))) for line in lines]
            pts={p for rec in recs for p in decode_record_points(rec)}
            cell_ids={y//8*40+x//8 for x,y in pts}
            f=FrameBuild(recs,[(i*8&255,i*8>>8,1) for i in sorted(cell_ids)],len(pts),len(pts),[],
                [(i&255,i>>8,1,((i%15+1)<<4)) for i in sorted(cell_ids)])
            self.assertIs(input_flip.frame(f),f)
            for horizontal,vertical in ((True,False),(False,True),(True,True)):
                kwargs=dict(height=height,flip_horizontal=horizontal,flip_vertical=vertical)
                got=input_flip.frame(f,**kwargs)
                expected={(255-x if horizontal else x,height-1-y if vertical else y) for x,y in pts}
                self.assertEqual(pixels(got),expected)
                self.assertEqual(clear_cells(got),{y//8*40+x//8 for x,y in expected})
                for old,color in cells(f.color_spans).items():
                    y,x=divmod(old,40)
                    new=(height//8-1-y if vertical else y)*40+(31-x if horizontal else x)
                    self.assertEqual(cells(got.color_spans)[new],color)
                twice=input_flip.frame(got,**kwargs)
                self.assertEqual(pixels(twice),pts)
                self.assertEqual(cells(twice.color_spans),cells(f.color_spans))

    def test_wire_and_authored_scene_pipeline(self):
        mesh=Mesh('asymmetric',[(-17,9,0),(11,4,0),(-7,-12,0)],[],[(0,1),(1,2)],line_colors=[2,7])
        cam=Camera(cx=101,cy=93)
        scene=SceneAnimation('scene',mesh,(SceneFrame(1,tuple((x,y,z+110) for x,y,z in mesh.vertices),
                Projection(cam.focal,cam.focal,cam.cx,cam.cy)),),25,1,Path('input.c643dscene'))
        for builder,args in ((build_frames,(mesh,1,cam)),(build_scene_frames,(scene,))):
            original=builder(*args,height=192,enable_source_colors=True)[0][0]
            for h,v in ((True,False),(False,True),(True,True)):
                actual=builder(*args,height=192,enable_source_colors=True,flip_horizontal=h,flip_vertical=v)[0][0]
                self.assertEqual(pixels(actual),{(255-x if h else x,191-y if v else y) for x,y in pixels(original)})

    def test_quantized_surface_and_right_padding(self):
        rng=np.random.default_rng(3)
        bits=rng.integers(0,2,(192,320),dtype=np.uint8)
        screen=rng.integers(0,256,(24,40),dtype=np.uint8)
        for h,v in ((True,False),(False,True),(True,True)):
            a,b=input_flip.surface(bits,screen,flip_horizontal=h,flip_vertical=v)
            expected=bits[:,:256][::(-1 if v else 1),::(-1 if h else 1)]
            np.testing.assert_array_equal(a[:,:256],expected)
            np.testing.assert_array_equal(a[:,256:],bits[:,256:])
            np.testing.assert_array_equal(b[:,:32],screen[:,:32][::(-1 if v else 1),::(-1 if h else 1)])
            np.testing.assert_array_equal(b[:,32:],screen[:,32:])
        self.assertEqual(input_flip.bounds([3,44,7,120],flip_horizontal=True,flip_vertical=True),[211,252,71,184])

    def test_filled_pipeline_matches_native_picture_and_coverage(self):
        mesh=Mesh('triangle',[(-21,16,0),(13,9,0),(-11,-17,0)],[(0,1,2)],face_colors=[2])
        base_bounds=[]
        original=filled_frames(mesh,1,Camera(cy=96),preset='material',coverage_bounds=base_bounds)[0]
        for h,v in ((True,False),(False,True),(True,True)):
            coverage=[]
            actual=filled_frames(mesh,1,Camera(cy=96),preset='material',coverage_bounds=coverage,flip_horizontal=h,flip_vertical=v)[0]
            self.assertEqual(pixels(actual),{(255-x if h else x,191-y if v else y) for x,y in pixels(original)})
            self.assertEqual(coverage,[input_flip.bounds(base_bounds[0],flip_horizontal=h,flip_vertical=v)])
            expected=input_flip.frame(FrameBuild(original.records,[],0,0,[],original.color_spans),flip_horizontal=h,flip_vertical=v)
            self.assertEqual(picture_bytes(actual),picture_bytes(expected))


if __name__=='__main__':unittest.main()
