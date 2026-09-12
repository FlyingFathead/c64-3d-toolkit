from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from c643d.objio import load_obj
from c643d.colors import nearest_c64_color_index
from c643d.surface_textures import Texture,load_textures,paint
from c643d.hors_v3 import prepare_colors, color_plan, color_plan_fits, literal_encoder
from c643d.pipeline import FrameBuild
from c643d.optimize import picture_bytes

class SurfaceTextureTests(unittest.TestCase):
    def test_uv_origin_repeat_and_clamp(self):
        t=Texture(np.array([[1,2],[3,4]],dtype=np.uint8),clamp=True)
        self.assertEqual(t.sample(np.array([[0,0],[1,1],[-2,3]])).tolist(),[3,2,1])
        t.clamp=False
        self.assertEqual(t.sample(np.array([[1.25,.25]])).tolist(),[3])

    def test_map_kd_uses_existing_nearest_palette_mapper_and_negative_uv_indices(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            Image.new('RGB',(2,2),(240,30,20)).save(p/'test color.png')
            (p/'test.mtl').write_text('newmtl face\nKd 1 1 1\nmap_Kd -s 2 2 -o 0 0 -clamp on "test color.png"\n')
            (p/'test.obj').write_text('mtllib test.mtl\nv 0 0 0\nv 1 0 0\nv 0 1 0\nvt 0 0\nvt 1 0\nvt 0 1\nusemtl face\nf -3/-3 -2/-2 -1/-1\n')
            mesh=load_obj(p/'test.obj');binding=load_textures(p/'test.obj',mesh)
            self.assertEqual(binding[0][0].pixels[0,0],nearest_c64_color_index((240,30,20)))
            self.assertEqual(binding[0][1][1],(1,0))
            self.assertEqual(binding[0][0].scale,(2,2))
            (p/'test.obj').write_text((p/'test.obj').read_text().replace('f -3/-3 -2/-2 -1/-1','f 1 2 3'))
            with self.assertRaisesRegex(ValueError,'missing OBJ vt'):
                load_textures(p/'test.obj',mesh)

    def test_perspective_correct_uvs(self):
        # At this sample, affine u is 0.405, but perspective u is about 0.068.
        # A four-column test texture distinguishes them without rounding ambiguity.
        p=np.zeros((192,256),dtype=np.uint8);owner=np.full((192,256),-1)
        owner[20,40]=0
        points=[(0,0,1.),(100,0,.1),(0,100,1.)]
        tex=Texture(np.array([[1,2,3,4]],dtype=np.uint8),clamp=True)
        binding=[(tex,{0:(0,0),1:(1,0),2:(0,1)})]
        paint(p,owner,points,[(0,0,1,2)],binding)
        self.assertEqual(p[20,40],1)
        paint(p,np.full((192,256),-1),points,[(0,0,1,2)],binding)

    def test_compact_dictionary_roundtrips_odd_cell_count(self):
        frame=FrameBuild([],[],0,0,[],[(2,0,2,0xb0),(9,0,1,0xf0)])
        active,runs=color_plan([frame])
        self.assertEqual(active,[2,3,9])
        palette=[0xb0,0xf0]
        packed,meta=literal_encoder(active,palette=palette)(frame)
        direct,dmeta=literal_encoder(active)(frame)
        self.assertEqual(meta,3)  # One clear-count byte plus two packed colour bytes.
        self.assertEqual(dmeta,4)
        indices=[n for byte in packed[1:meta] for n in (byte>>4,byte&15)][:len(active)]
        self.assertEqual(bytes(palette[i] for i in indices),direct[1:dmeta])

    def test_compact_metadata_can_fit_when_literal_exceeds_cache(self):
        frame=FrameBuild([],[(0,0,1)]*60,0,0,[],[(0,0,255,0xb0),(255,0,255,0xb0),(254,1,255,0xb0),(253,2,135,0xb0)])
        active,runs=color_plan([frame])
        self.assertEqual(len(active),900)
        self.assertFalse(color_plan_fits([frame],active,runs))
        self.assertTrue(color_plan_fits([frame],active,runs,[0xb0]))
        packed,meta=literal_encoder(active,palette=[0xb0])(frame)
        self.assertLessEqual(meta,1024)
        with self.assertRaisesRegex(ValueError,'metadata exceeds'):
            literal_encoder(active)(frame)

    def test_v3_color_coverage_is_independent_of_reused_buffer_contents(self):
        frames=[FrameBuild([],[],0,0,[],[(2,0,3,0xb0)]),
                FrameBuild([],[],0,0,[],[(4,0,2,0xf0)]),
                FrameBuild([],[],0,0,[],[])]
        prepared,policy=prepare_colors(frames)
        buffers=[bytearray([16])*960 for _ in range(3)]
        for i,fi in enumerate([0,1,2,2,0,1,0,2,1,1,0,2]):
            buf=buffers[i%3]
            for lo,hi,n,value in prepared[fi].color_spans:
                start=lo+256*hi;buf[start:start+n]=bytes([value])*n
            self.assertEqual(bytes(buf),picture_bytes(frames[fi])[7680:])
        self.assertFalse(policy['previous_picture_dependency'])

if __name__=='__main__':unittest.main()
