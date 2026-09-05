from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .sceneio import SceneAnimation, load_scene
from .toolchain import platform_key, resolve_executable


def install_instructions(*, system: str | None = None) -> tuple[str, ...]:
    key=platform_key(system)
    if key=='windows':
        return (
            'Install with WinGet: winget install -e --id BlenderFoundation.Blender',
            'Or download Blender: https://www.blender.org/download/',
            r'Then retry, or pass --blender "C:\Program Files\Blender Foundation\Blender 4.x\blender.exe".',
        )
    if key=='macos':
        return (
            'Install with Homebrew: brew install --cask blender',
            'Or download Blender: https://www.blender.org/download/',
            'Then retry, or pass --blender /Applications/Blender.app.',
        )
    return (
        'Recommended current LTS: https://www.blender.org/download/',
        'Current Snap channel: sudo snap install blender --classic',
        'Ubuntu 24.04 repository fallback (Blender 4.0.2): sudo apt install blender',
        'Then retry, or pass --blender /path/to/blender.',
    )


def blender_frame_plan(
    start: int,
    end: int,
    sample_step: int,
    *,
    scene_start: int,
    simulation_start: int | None=None,
) -> tuple[range,tuple[int,...]]:
    """Return sequential evaluation frames and the subset to capture."""
    if start>end:
        raise ValueError('frame start is after frame end')
    if sample_step<1:
        raise ValueError('sample step must be at least 1')
    origins=[start,int(scene_start)]
    if simulation_start is not None:
        origins.append(int(simulation_start))
    evaluation_start=min(origins)
    captures=tuple(range(start,end+1,sample_step))
    return range(evaluation_start,end+1),captures


def probe_blender(executable: str) -> str:
    """Prove that Blender starts headlessly and its bundled ``bpy`` imports."""
    marker='C643D_BPY_OK:'
    expression=f'import bpy; print("{marker}" + bpy.app.version_string)'
    try:
        completed=subprocess.run(
            [executable,'--background','--factory-startup','--disable-autoexec',
             '--python-exit-code','1','--python-expr',expression],
            check=False,capture_output=True,text=True,timeout=45,
        )
    except (OSError,subprocess.TimeoutExpired) as e:
        raise RuntimeError(f'Blender/bpy preflight could not run: {e}') from e
    combined='\n'.join((completed.stdout or '',completed.stderr or ''))
    version=next((line.split(marker,1)[1].strip() for line in combined.splitlines() if marker in line),None)
    if completed.returncode or not version:
        diagnostic_lines=[line.rstrip() for line in combined.splitlines() if line.strip()]
        detail='\n'.join(diagnostic_lines[-8:]) if diagnostic_lines else 'no diagnostic output'
        raise RuntimeError(
            f'Blender/bpy preflight failed (exit {completed.returncode}):\n{detail}\n'
            'hint: verify with: blender --background --disable-autoexec --python-expr '
            '\'import bpy; print(bpy.app.version_string)\''
        )
    return version


def require_blender(spec: str='blender', *, system: str | None = None) -> tuple[str,str]:
    found=resolve_executable(spec,'blender',system=system)
    if found:
        return found,probe_blender(found)
    lines=[f'error: Blender not found as {spec!r}; --blend requires Blender itself to read .blend files.']
    lines.extend(f'hint: {line}' for line in install_instructions(system=system))
    raise RuntimeError('\n'.join(lines))


def export_blend_scene(
    blend_path: str | Path,
    output_path: str | Path,
    *,
    blender: str='blender',
    frame_start: int | None=None,
    frame_end: int | None=None,
    sample_step: int=1,
    system: str | None=None,
    root: str | Path | None=None,
    blender_is_verified: bool=False,
    viewport_height: int=144,
    max_frames: int=255,
) -> Path:
    source=Path(blend_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f'Blender scene not found: {source}')
    if source.suffix.lower()!='.blend':
        raise ValueError(f'--blend expects a .blend file: {source}')
    if sample_step<1:
        raise ValueError('--sample-step must be at least 1')
    if viewport_height<8 or viewport_height>200 or viewport_height%8:
        raise ValueError('viewport height must be a multiple of 8 from 8..200')
    executable=str(blender) if blender_is_verified else require_blender(blender,system=system)[0]
    project_root=Path(root).resolve() if root else Path(__file__).resolve().parents[2]
    script=project_root/'tools'/'blender_export.py'
    output=Path(output_path).resolve()
    cmd=[
        executable,'--background','--disable-autoexec',str(source),
        '--python-exit-code','1','--python',str(script),'--',
        '--output',str(output),'--sample-step',str(sample_step),
        '--viewport-height',str(viewport_height),'--max-frames',str(max_frames),
    ]
    if frame_start is not None:
        cmd.extend(['--frame-start',str(frame_start)])
    if frame_end is not None:
        cmd.extend(['--frame-end',str(frame_end)])
    print('blender export:',' '.join(cmd),flush=True)
    completed=subprocess.run(cmd,cwd=project_root,check=False)
    if completed.returncode:
        raise RuntimeError(f'Blender scene export failed with exit code {completed.returncode}')
    if not output.is_file():
        raise RuntimeError('Blender reported success but did not create the scene export')
    return output


def load_blend_scene(blend_path: str | Path, output_path: str | Path, **kwargs) -> SceneAnimation:
    return load_scene(export_blend_scene(blend_path,output_path,**kwargs))
