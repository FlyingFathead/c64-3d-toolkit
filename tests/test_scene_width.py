"""Full bitmap-width projection and clear-span boundaries."""
import unittest
from pathlib import Path
from tools.c643d.mesh import Mesh
from tools.c643d.pipeline import build_scene_frames,decode_record_points
from tools.c643d.sceneio import SceneAnimation,SceneFrame,Projection
from tools.c643d.clearplan import selective_clear
from tools.c643d.hors_v3 import compact_clear_spans


class SceneWidthTests(unittest.TestCase):
    def test_all_edges_and_crossing_byte_255(self):
        vertices=((-200,0,100),(200,0,100),(0,-150,100),(0,150,100))
        mesh=Mesh('cross',list(vertices),[],[(0,1),(2,3)],line_colors=[2,3])
        scene=SceneAnimation('cross',mesh,(SceneFrame(1,vertices,Projection(100,100,160,96)),),25,1,Path('cross.c643dscene'),320)
        frame=build_scene_frames(scene,height=192,enable_source_colors=True)[0][0]
        pts={p for r in frame.records for p in decode_record_points(r)}
        self.assertTrue({(0,96),(255,96),(256,96),(319,96),(160,0),(160,191)}<=pts)
        self.assertTrue(all(n<=32 for lo,hi,n in frame.clear_spans))
        selected,_=selective_clear(frame)
        compact=compact_clear_spans(selected)
        for lo,hi,n in compact.clear_spans:
            self.assertLessEqual(n,255 if hi&128 else 32)
        for h,v in ((True,False),(False,True),(True,True)):
            flipped=build_scene_frames(scene,height=192,enable_source_colors=True,flip_horizontal=h,flip_vertical=v)[0][0]
            self.assertEqual({p for r in flipped.records for p in decode_record_points(r)},
                {(319-x if h else x,191-y if v else y) for x,y in pts})
            selective_clear(flipped)  # rejects unsafe >32-cell records


if __name__=='__main__':unittest.main()
