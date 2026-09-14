import contextlib
import importlib.util
import io
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from tools.c643d.blender_colors import material_rgb_bytes, material_color_index
from tools.c643d.cli import make_parser
from tools.c643d.configure import configure_blender_color_space, save_blender_color_space
from tools.c643d.toolchain import load_toolchain_settings

ROOT=Path(__file__).resolve().parents[1]


class BlenderColorTests(unittest.TestCase):
    def test_recorded_red_interpretation(self):
        rgb=tuple(v/255 for v in (152,53,45))
        self.assertEqual(material_rgb_bytes(rgb,'srgb'),(152,53,45))
        self.assertEqual(material_rgb_bytes(rgb,'linear'),(203,126,117))
        self.assertEqual(material_color_index(rgb,'srgb'),2)
        self.assertEqual(material_color_index(rgb,'linear'),8)

    def test_linear_default_preserves_conversion(self):
        for value in (0.,.0031308,.03,.2,.8,1.,2.,-.1):
            expected=12.92*max(0.,value) if value<=.0031308 else 1.055*max(0.,value)**(1/2.4)-.055
            self.assertEqual(material_rgb_bytes((value,)*3),(max(0,min(255,round(expected*255))),)*3)

    def test_invalid_mode_and_nonfinite_values_fail(self):
        for value in (math.nan,math.inf,-math.inf):
            with self.assertRaises(ValueError):material_rgb_bytes((0,value,0))
        with self.assertRaises(ValueError):material_rgb_bytes((0,0,0),'guess')

    def test_exporter_uses_unlinked_principled_and_explicit_override(self):
        spec=importlib.util.spec_from_file_location('color_export_test',ROOT/'tools/blender_export.py')
        module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'bpy':SimpleNamespace()}):spec.loader.exec_module(module)
        class Material(dict):pass
        obj=Material();mat=Material()
        rgb=tuple(v/255 for v in (152,53,45))+(1.,)
        mat.diffuse_color=(0,1,0,1);mat.use_nodes=True
        shader=SimpleNamespace(type='BSDF_PRINCIPLED',inputs={'Base Color':SimpleNamespace(is_linked=False,default_value=rgb)})
        output=SimpleNamespace(type='OUTPUT_MATERIAL',is_active_output=True,inputs={'Surface':SimpleNamespace(is_linked=True,links=[SimpleNamespace(from_node=shader)])})
        mat.node_tree=SimpleNamespace(nodes=[output]);mat.name='material'
        self.assertEqual(module._property_color(obj,mat,'srgb'),2)
        self.assertEqual(module._property_color(obj,mat,'linear'),8)
        mat['c643d_color']='red'
        self.assertEqual(module._property_color(obj,mat,'linear'),2)
        self.assertEqual(module._property_color(obj,mat,'srgb'),2)


class BlenderConfigurationTests(unittest.TestCase):
    def test_ini_and_cli_precedence(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'toolkit.ini';save_blender_color_space(path,'srgb')
            settings=load_toolchain_settings(path)
            p=make_parser(settings)
            self.assertEqual(p.parse_args(['build']).blender_color_space,'srgb')
            self.assertEqual(p.parse_args(['build','--blender-color-space','linear']).blender_color_space,'linear')
            self.assertEqual(load_toolchain_settings(None).blender_color_space,'linear')

    def test_writer_preserves_other_settings_comments_and_single_section(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'toolkit.ini'
            prefix='# keep this comment\n[toolchain]\nblender = custom blender\n\n'
            tail='[windows]\nvice = custom.exe\n'
            path.write_text(prefix+'[render_defaults]\n# keep me too\nbackground_color = blue\n\n'+tail)
            save_blender_color_space(path,'srgb');save_blender_color_space(path,'linear')
            text=path.read_text()
            self.assertTrue(text.startswith(prefix) and text.endswith(tail))
            self.assertIn('# keep me too',text)
            self.assertIn('background_color = blue',text)
            self.assertEqual(text.count('blender_color_space ='),1)
            self.assertEqual(text.count('[render_defaults]'),1)

    def test_interactive_chooser_and_default(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'toolkit.ini'
            with contextlib.redirect_stdout(io.StringIO()):
                configure_blender_color_space(path,'ask',input_fn=lambda prompt:'2')
                self.assertEqual(load_toolchain_settings(path).blender_color_space,'srgb')
                configure_blender_color_space(path,'ask',current='srgb',input_fn=lambda prompt:'')
            self.assertEqual(load_toolchain_settings(path).blender_color_space,'srgb')

    def test_invalid_selection_and_no_config_do_not_write(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'toolkit.ini'
            with self.assertRaises(ValueError):save_blender_color_space(path,'guess')
            self.assertFalse(path.exists())
            with self.assertRaises(ValueError):configure_blender_color_space(None,'srgb')

    def test_direct_cli_creates_config_without_build_dependencies(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'new.ini'
            for flags,expected in ((['--configure-blender-color-space','srgb'],'srgb'),
                                   (['configure','--blender-color-space','linear'],'linear'),
                                   (['--configure-blender-color','srgb'],'srgb')):
                result=subprocess.run([sys.executable,'-S',str(ROOT/'c643d.py'),*flags,'--config',str(path)],input='',text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertIn('Saved Blender colour space',result.stdout)
                self.assertEqual(load_toolchain_settings(path).blender_color_space,expected)

    def test_cli_interactive_and_no_config_rejection(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'new.ini'
            result=subprocess.run([sys.executable,'-S',str(ROOT/'c643d.py'),'--configure-blender-color-space','--config',str(path)],input='2\n',text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(load_toolchain_settings(path).blender_color_space,'srgb')
            result=subprocess.run([sys.executable,'-S',str(ROOT/'c643d.py'),'--configure-blender-color-space','linear','--no-config'],input='',text=True,capture_output=True)
            self.assertEqual(result.returncode,2)
            self.assertIn('--no-config',result.stderr)

    def test_warning_suppression_reaches_blender_export(self):
        from tools.c643d.blender import export_blend_scene
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'scene.blend';source.touch()
            output=Path(td)/'scene.c643dscene'
            def run(cmd,**kwargs):
                self.assertIn('--ignore-warnings',cmd)
                self.assertEqual(cmd[cmd.index('--blender-color-space')+1],'srgb')
                output.write_text('{}')
                return SimpleNamespace(returncode=0)
            with patch('tools.c643d.blender.subprocess.run',side_effect=run),contextlib.redirect_stdout(io.StringIO()):
                export_blend_scene(source,output,blender='blender',blender_is_verified=True,ignore_warnings=True,blender_color_space='srgb')

if __name__=='__main__':unittest.main()
