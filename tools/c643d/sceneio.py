from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .mesh import Mesh


@dataclass(frozen=True)
class Projection:
    """Pinhole projection for camera-space vertices.

    Camera space uses +X right, +Y up, and +Z forward.  ``fx`` and ``fy`` are
    focal lengths in C64 bitmap pixels; ``cx``/``cy`` are the principal point.
    """

    fx: float
    fy: float
    cx: float = 128.0
    cy: float = 72.0


@dataclass(frozen=True)
class SceneFrame:
    source_frame: int
    vertices: tuple[tuple[float, float, float], ...]
    projection: Projection


@dataclass(frozen=True)
class SceneAnimation:
    name: str
    mesh: Mesh
    frames: tuple[SceneFrame, ...]
    source_fps: float
    sample_step: int
    source: Path


def _number(value, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{where} must be a number')
    return float(value)


def _index_list(value, where: str, *, minimum: int) -> list[tuple[int, ...]]:
    if not isinstance(value, list):
        raise ValueError(f'{where} must be a list')
    out=[]
    for i,item in enumerate(value):
        if not isinstance(item,list) or len(item)<minimum:
            raise ValueError(f'{where}[{i}] must contain at least {minimum} vertex indices')
        if any(isinstance(v,bool) or not isinstance(v,int) for v in item):
            raise ValueError(f'{where}[{i}] contains a non-integer vertex index')
        out.append(tuple(item))
    return out


def _colors(value, where: str) -> list[int | None]:
    if value is None:
        return []
    if not isinstance(value,list):
        raise ValueError(f'{where} must be a list')
    out=[]
    for i,color in enumerate(value):
        if color is None:
            out.append(None)
        elif isinstance(color,int) and not isinstance(color,bool) and 0<=color<=15:
            out.append(color)
        else:
            raise ValueError(f'{where}[{i}] must be null or a C64 colour index 0..15')
    return out


def load_scene(path: str | Path) -> SceneAnimation:
    """Load and validate the Blender-neutral ``.c643dscene`` interchange file."""

    source=Path(path)
    try:
        data=json.loads(source.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        raise ValueError(f'invalid scene JSON at line {e.lineno}, column {e.colno}: {e.msg}') from e
    if not isinstance(data,dict):
        raise ValueError('scene root must be a JSON object')
    if data.get('format')!='c643dscene' or data.get('version')!=1:
        raise ValueError('unsupported scene format/version; expected c643dscene version 1')

    topology=data.get('topology')
    if not isinstance(topology,dict):
        raise ValueError('scene topology must be a JSON object')
    faces=_index_list(topology.get('faces',[]),'topology.faces',minimum=3)
    line_edges=_index_list(topology.get('line_edges',[]),'topology.line_edges',minimum=2)
    if any(len(edge)!=2 for edge in line_edges):
        raise ValueError('each topology.line_edges entry must contain exactly two indices')
    face_colors=_colors(topology.get('face_colors'),'topology.face_colors')
    line_colors=_colors(topology.get('line_colors'),'topology.line_colors')
    if face_colors and len(face_colors)!=len(faces):
        raise ValueError('topology.face_colors length must match topology.faces')
    if line_colors and len(line_colors)!=len(line_edges):
        raise ValueError('topology.line_colors length must match topology.line_edges')

    raw_frames=data.get('frames')
    if not isinstance(raw_frames,list) or not raw_frames:
        raise ValueError('scene must contain at least one frame')
    frames=[]; vertex_count=None
    for fi,raw in enumerate(raw_frames):
        if not isinstance(raw,dict):
            raise ValueError(f'frames[{fi}] must be a JSON object')
        raw_vertices=raw.get('vertices')
        if not isinstance(raw_vertices,list) or not raw_vertices:
            raise ValueError(f'frames[{fi}].vertices must be a non-empty list')
        vertices=[]
        for vi,p in enumerate(raw_vertices):
            if not isinstance(p,list) or len(p)!=3:
                raise ValueError(f'frames[{fi}].vertices[{vi}] must contain x, y, z')
            vertices.append(tuple(_number(v,f'frames[{fi}].vertices[{vi}]') for v in p))
        if vertex_count is None:
            vertex_count=len(vertices)
        elif len(vertices)!=vertex_count:
            raise ValueError(
                f'frame topology changed: frame {fi} has {len(vertices)} vertices; expected {vertex_count}'
            )
        projection=raw.get('projection')
        if not isinstance(projection,dict):
            raise ValueError(f'frames[{fi}].projection must be a JSON object')
        proj=Projection(
            _number(projection.get('fx'),f'frames[{fi}].projection.fx'),
            _number(projection.get('fy'),f'frames[{fi}].projection.fy'),
            _number(projection.get('cx',128.0),f'frames[{fi}].projection.cx'),
            _number(projection.get('cy',72.0),f'frames[{fi}].projection.cy'),
        )
        if proj.fx<=0 or proj.fy<=0:
            raise ValueError(f'frames[{fi}] projection focal lengths must be positive')
        source_frame=raw.get('source_frame',fi)
        if isinstance(source_frame,bool) or not isinstance(source_frame,int):
            raise ValueError(f'frames[{fi}].source_frame must be an integer')
        frames.append(SceneFrame(source_frame,tuple(vertices),proj))

    assert vertex_count is not None
    for where,items in (('face',faces),('line edge',line_edges)):
        for i,item in enumerate(items):
            if any(v<0 or v>=vertex_count for v in item):
                raise ValueError(f'topology {where} {i} references a vertex outside 0..{vertex_count-1}')
    mesh=Mesh(
        str(data.get('name') or source.stem).upper(),list(frames[0].vertices),faces,
        [tuple(edge) for edge in line_edges],face_colors,line_colors,
    )
    meta=data.get('source') if isinstance(data.get('source'),dict) else {}
    source_fps=_number(meta.get('fps',0.0),'source.fps')
    sample_step=meta.get('sample_step',1)
    if isinstance(sample_step,bool) or not isinstance(sample_step,int) or sample_step<1:
        raise ValueError('source.sample_step must be a positive integer')
    return SceneAnimation(mesh.name,mesh,tuple(frames),source_fps,sample_step,source.resolve())
