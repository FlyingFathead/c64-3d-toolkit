"""Camera crossing, occlusion, empty timing samples and legacy preservation."""
import contextlib
import io
import unittest
from pathlib import Path
from tools.c643d.clipping import clip_line_near, project_clipped_triangle
from tools.c643d.mesh import Mesh
from tools.c643d.pipeline import Camera, build_frames, build_scene_frames, decode_record_points
from tools.c643d.sceneio import Projection, SceneAnimation, SceneFrame


def scene(vertices, edges=(), faces=(), colors=(), width=256):
    mesh=Mesh('CAMERA CROSSING',list(vertices[0]),list(faces),list(edges),line_colors=list(colors))
    return SceneAnimation(mesh.name,mesh,tuple(
        SceneFrame(i+1,tuple(v),Projection(80,80,width/2,72)) for i,v in enumerate(vertices)
    ),25,1,Path('camera-crossing.c643dscene'),width)


def points(frame):
    return {p for record in frame.records for p in decode_record_points(record)}


class CameraClippingTests(unittest.TestCase):
    def test_line_near_keeps_direction_and_visible_segment(self):
        a=(-1.,0.,-1.); b=(1.,1.,1.)
        forward=clip_line_near(a,b,near=.1)
        self.assertEqual(forward[1],b)
        reverse=tuple(reversed(clip_line_near(b,a,near=.1)))
        for p,q in zip(forward,reverse):
            for v,w in zip(p,q):self.assertAlmostEqual(v,w)
        self.assertAlmostEqual(forward[0][2],.1)
        self.assertIsNone(clip_line_near(a,(-2,1,0),near=.1))

    def test_crossing_edge_retains_pixels_and_source_color(self):
        s=scene([((-1.,0.,-1.),(1.,1.,2.))],[(0,1)],colors=[2],width=320)
        frame=build_scene_frames(s,height=192,enable_source_colors=True,ignore_warnings=True)[0][0]
        self.assertTrue(points(frame))
        self.assertEqual(frame.color_palette,(2,))
        self.assertTrue(all(0<=x<320 and 0<=y<192 for x,y in points(frame)))

    def test_vertices_on_camera_plane_do_not_divide_by_zero(self):
        s=scene([((0.,1.,0.),(1.,1.,2.))],[(0,1)])
        frame=build_scene_frames(s,ignore_warnings=True)[0][0]
        self.assertTrue(points(frame))

    def test_disappear_and_reappear_preserves_samples(self):
        visible=((-1.,0.,2.),(1.,0.,2.))
        hidden=((-1.,0.,-2.),(1.,0.,-2.))
        s=scene([visible,hidden,hidden,visible],[(0,1)],colors=[2])
        frames,edges=build_scene_frames(s,enable_source_colors=True,ignore_warnings=True)
        self.assertEqual((len(frames),edges),(4,1))
        self.assertEqual([bool(f.records) for f in frames],[True,False,False,True])
        self.assertEqual(frames[0],frames[3])
        for f in frames[1:3]:
            self.assertEqual((f.records,f.clear_spans,f.color_spans,f.unique_pixels),([],[],[],0))

    def test_all_behind_and_all_outside_frames_are_valid(self):
        s=scene([((-1.,0.,-2.),(1.,0.,-2.)),((100.,0.,1.),(102.,0.,1.))],[(0,1)])
        frames,_=build_scene_frames(s,ignore_warnings=True)
        self.assertEqual([f.unique_pixels for f in frames],[0,0])

    def test_near_clipped_triangle_still_occludes_unrelated_line(self):
        # The front part covers the centre; one corner is behind the camera.
        verts=((-3.,-3.,2.),(3.,-3.,2.),(0.,3.,-1.),(-.25,0.,4.),(.25,0.,4.))
        s=scene([verts],[(3,4)],[(0,1,2)])
        frame=build_scene_frames(s,ignore_warnings=True)[0][0]
        self.assertFalse(any(y==72 and 123<=x<=133 for x,y in points(frame)))
        no_face=scene([verts],[(3,4)])
        self.assertTrue(any(y==72 and 123<=x<=133 for x,y in points(build_scene_frames(no_face,ignore_warnings=True)[0][0])))

    def test_triangle_clip_interpolates_reciprocal_depth(self):
        tris=project_clipped_triangle([(-1,-1,-1),(1,-1,2),(0,1,2)],
            lambda p:(128+80*p[0]/p[2],72-80*p[1]/p[2],1/p[2]),width=256,height=144)
        self.assertTrue(tris)
        for tri in tris:
            for x,y,q in tri:
                self.assertTrue(-1e-8<=x<=256+1e-8 and -1e-8<=y<=144+1e-8)
                self.assertGreater(q,0)

    def test_one_summary_and_explicit_suppression(self):
        s=scene([((-1.,0.,-2.),(1.,0.,-2.))]*9,[(0,1)])
        out=io.StringIO(); stats={}
        with contextlib.redirect_stderr(out):
            build_scene_frames(s,clipping_stats=stats)
        self.assertEqual(out.getvalue().count('WARNING:'),1)
        self.assertIn('9 invisible frames retained',out.getvalue())
        self.assertEqual(stats['empty_frames'],9)
        with contextlib.redirect_stderr(io.StringIO()) as quiet:
            build_scene_frames(s,ignore_warnings=True)
        self.assertEqual(quiet.getvalue(),'')

    def test_in_front_scene_matches_legacy_bytes_and_guard(self):
        vertices=((-1.,0.,2.),(1.,0.,2.))
        s=scene([vertices],[(0,1)],colors=[2])
        legacy=build_frames(s.mesh,1,Camera(0,80,128,72),animation='recede',animation_travel=0,
            enable_source_colors=True)[0]
        self.assertEqual(build_scene_frames(s,enable_source_colors=True)[0],legacy)
        hidden=scene([((-1.,0.,-2.),(1.,0.,-2.))],[(0,1)])
        with self.assertRaisesRegex(RuntimeError,'near plane'):
            build_frames(hidden.mesh,1,Camera(0,80,128,72))


if __name__=='__main__':unittest.main()
