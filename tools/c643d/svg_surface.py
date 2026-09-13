"""Bake SVG paint and an alpha-defined solid for the HORS-V3 surface pipeline.

The old dependency-free wire importer remains in svgio. Filled SVGs use
CairoSVG on the host, then exact rectangles over a declared-resolution mask.
This preserves holes without fan-triangulating concave compound paths.
"""
from dataclasses import dataclass
import hashlib
from io import BytesIO
import math
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import url2pathname

import numpy as np
from PIL import Image

from .colors import c64_color_name, nearest_c64_color_index
from .mesh import Mesh
from .surface_textures import Texture


@dataclass
class SvgSurface:
    mesh: Mesh
    bindings: list
    report: dict
    c64_color: str
    two_sided: bool


def _runs(row):
    edges = np.flatnonzero(np.diff(np.r_[False, row, False].astype(np.int8)))
    return [(int(a), int(b)) for a, b in zip(edges[::2], edges[1::2])]


def mask_rectangles(mask):
    """Disjoint rectangles covering every opaque texel exactly once."""
    active = {}
    for y in range(mask.shape[0] + 1):
        runs = set(_runs(mask[y])) if y < mask.shape[0] else set()
        for (x0, x1), y0 in sorted(active.items()):
            if (x0, x1) not in runs:
                yield x0, y0, x1, y
        active = {run: active.get(run, y) for run in sorted(runs)}


def _dimension(value):
    match = re.fullmatch(r'\s*(\d*\.?\d+)\s*(px|in|cm|mm|pt|pc)?\s*', value or '')
    if not match:
        return None
    return float(match[1]) * {None: 1, 'px': 1, 'in': 96, 'cm': 96/2.54,
                              'mm': 96/25.4, 'pt': 96/72, 'pc': 16}[match[2]]


def bake_svg(path, *, resolution=512, keep_background=True, outlines_only=False):
    try:
        import cairosvg
        from cairosvg.surface import PNGSurface
        from cairosvg.url import fetch
        from defusedxml import ElementTree as ET
    except (ImportError, OSError) as exc:
        raise ValueError('SVG fills need CairoSVG and Cairo on the host; see docs/SVG_PIPELINE.md (python -m pip install -r requirements-svg.txt)') from exc
    if not 16 <= resolution <= 2048:
        raise ValueError('--svg-texture-size must be 16..2048')
    path = Path(path).resolve()
    root = ET.fromstring(path.read_bytes())
    vb = [float(v) for v in re.split(r'[\s,]+', root.get('viewBox', '').strip()) if v]
    width, height = _dimension(root.get('width')), _dimension(root.get('height'))
    if not width or not height:
        if len(vb) != 4:
            raise ValueError('SVG fills need a viewBox or explicit width and height')
        width, height = vb[2:]
    if not all(math.isfinite(v) and v > 0 for v in (width, height)):
        raise ValueError('SVG width and height must be positive and finite')
    warnings = []
    for element in root.iter():
        tag = element.tag.rsplit('}', 1)[-1]
        if tag in ('filter', 'foreignObject', 'script', 'animate', 'animateTransform', 'set'):
            raise ValueError(f'SVG <{tag}> is not supported by the static fill importer; bake it into an image first')
        if tag == 'text' and not warnings:
            warnings.append('SVG text uses installed host fonts; convert text to paths for portable lettering')
    removed = 0
    # Match the existing logo-import convention, but offer an explicit opt-out.
    canvas = vb if len(vb) == 4 else [0, 0, width, height]
    if not keep_background:
        for child in list(root):
            if child.tag.rsplit('}', 1)[-1] != 'rect' or child.get('transform'):
                continue
            values = []
            for index,(key,default) in enumerate((('x','0'),('y','0'),('width',''),('height',''))):
                value=child.get(key,default).strip()
                if value.endswith('%'):
                    try: value=float(value[:-1])*canvas[2+(index%2)]/100
                    except ValueError: value=None
                else: value=_dimension(value)
                values.append(value)
            if all(a is not None and abs(a-b) < 1e-6 for a, b in zip(values, canvas)):
                root.remove(child)
                removed += 1
    resources = []

    def local_fetch(url, resource_type):
        parsed = urlsplit(url)
        if parsed.scheme == 'data':
            return fetch(url, resource_type)
        if parsed.scheme not in ('', 'file') or parsed.netloc:
            raise ValueError('SVG resources must be local files or embedded data; download remote images/styles first')
        local = Path(url2pathname(parsed.path))
        if not local.is_absolute():
            local = path.parent / local
        try:
            data = local.read_bytes()
        except OSError as exc:
            raise ValueError(f'SVG resource is missing or unreadable: {local.name}') from exc
        resources.append(dict(file=local.name, sha256=hashlib.sha256(data).hexdigest()))
        return data

    w = max(1, round(resolution * width / max(width, height)))
    h = max(1, round(resolution * height / max(width, height)))
    class OutlineSurface(PNGSurface):
        def draw(self, node):
            # Operate on computed paint after <use> expansion and CSS
            # inheritance. Restore the node afterwards so reused definitions
            # keep their original paint for other instances.
            parent = node
            while parent is not None:
                if parent.tag in ('clipPath', 'mask'):
                    return super().draw(node)
                parent = getattr(parent, 'parent', None)
            if node.tag == 'image':
                raise ValueError('--svg-outlines-only needs vector shapes; trace embedded images first')
            shapes = {'path', 'rect', 'circle', 'ellipse', 'line', 'polygon',
                      'polyline', 'text', 'tspan'}
            if node.tag not in shapes:
                return super().draw(node)
            original = dict(node)
            stroke = node.get('stroke', 'none')
            node['fill'] = 'none'
            node['stroke'] = 'white' if stroke == 'none' else stroke
            try:
                return super().draw(node)
            finally:
                node.clear()
                node.update(original)

    surface_type = OutlineSurface if outlines_only else PNGSurface
    png = surface_type.convert(bytestring=ET.tostring(root), url=path.as_uri(),
        output_width=w, output_height=h, url_fetcher=local_fetch)
    with Image.open(BytesIO(png)) as image:
        rgba = np.array(image.convert('RGBA'))
    return rgba, dict(source=path.name, source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        baker='CairoSVG', baker_version=cairosvg.__version__, raster_size=[w, h],
        background_rectangles_removed=removed, outlines_only=outlines_only,
        resources=resources, warnings=warnings)


def surface_from_rgba(rgba, name, *, depth=5.0, alpha_threshold=128, texture_path=None, report=None, override_color=None):
    if not 1 <= alpha_threshold <= 255:
        raise ValueError('--svg-alpha-threshold must be 1..255')
    if not math.isfinite(depth) or depth < 0:
        raise ValueError('--svg-depth must be finite and nonnegative')
    report = dict(report or {})
    mask = rgba[:, :, 3] >= alpha_threshold
    ys, xs = np.nonzero(mask)
    if not len(xs):
        raise ValueError('SVG has no painted area at this alpha threshold; use --svg-keep-background for a canvas-only rectangle')
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)
    rgba = rgba[y0:y1, x0:x1]
    mask = mask[y0:y1, x0:x1]
    h, w = mask.shape
    if texture_path:
        path = Path(texture_path)
        with Image.open(path) as image:
            rgba = np.array(image.convert('RGBA').resize((w, h), Image.Resampling.LANCZOS))
        report['texture'] = dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    # The C64 runtime has binary coverage. Partial paint opacity is baked on
    # black before palette matching; fully transparent holes have no faces.
    rgb = np.rint(rgba[:, :, :3].astype(float) * rgba[:, :, 3:4] / 255).astype(np.uint8)
    unique, inverse = np.unique(rgb.reshape(-1, 3), axis=0, return_inverse=True)
    palette = np.array([nearest_c64_color_index(tuple(map(int, v))) for v in unique], dtype=np.uint8)
    pixels = palette[inverse].reshape(h, w)
    if override_color is not None:
        if not 0 <= override_color <= 15:
            raise ValueError('SVG override colour must be a C64 palette index')
        pixels.fill(override_color)
    texture = Texture(pixels, clamp=True)
    histogram = np.bincount(pixels[mask], minlength=16)
    vertices, faces, colors, bindings, vertex_ids = [], [], [], [], {}
    z = depth * max(w, h) / 92 / 2

    def face(corners, uv=None, color=None):
        ids = []
        for x, y, zz in corners:
            vertex = (x, -y, zz)
            if vertex not in vertex_ids:
                vertex_ids[vertex] = len(vertices)
                vertices.append(vertex)
            ids.append(vertex_ids[vertex])
        faces.append(tuple(ids))
        colors.append(int(np.argmax(histogram)) if color is None else int(color))
        coords = uv or [(x/w, 1-y/h) for x, y, zz in corners]
        bindings.append((texture, dict(zip(ids, coords))))

    rects = list(mask_rectangles(mask))
    for left, top, right, bottom in rects:
        cap = [(left, top, -z), (right, top, -z), (right, bottom, -z), (left, bottom, -z)]
        color = int(pixels[top, left])
        face(cap, color=color)
        if z:
            face([(x, y, z) for x, y, zz in reversed(cap)], color=color)
    cap_faces = len(faces)
    if z:
        # Boundary-only walls, including every hole; merge straight runs.
        padded = np.pad(mask, 1)
        for side, neighbour in [('top', padded[:-2, 1:-1]), ('bottom', padded[2:, 1:-1])]:
            for y, row in enumerate(mask & ~neighbour):
                yy = y if side == 'top' else y+1
                for left, right in _runs(row):
                    corners = [(left, yy, -z), (left, yy, z), (right, yy, z), (right, yy, -z)]
                    uv = [(x/w, 1-(y+.5)/h) for x, _, _ in corners]
                    if side == 'bottom':
                        corners.reverse(); uv.reverse()
                    face(corners, uv, pixels[y, left])
        for side, neighbour in [('left', padded[1:-1, :-2]), ('right', padded[1:-1, 2:])]:
            for x, column in enumerate((mask & ~neighbour).T):
                xx = x if side == 'left' else x+1
                for top, bottom in _runs(column):
                    corners = [(xx, top, -z), (xx, bottom, -z), (xx, bottom, z), (xx, top, z)]
                    uv = [((x+.5)/w, 1-y/h) for _, y, _ in corners]
                    if side == 'right':
                        corners.reverse(); uv.reverse()
                    face(corners, uv, pixels[top, x])
    report.update(crop=[x0, y0, x1, y1], texture_size=[w, h], alpha_threshold=alpha_threshold,
        opaque_texels=int(mask.sum()), cap_rectangles=len(rects), wall_quads=len(faces)-cap_faces,
        depth=depth, geometry='disjoint alpha-mask rectangles and boundary walls; no hole-filling fan',
        opacity='binary coverage at threshold; partial paint composited on black',
        source_rgb_colors=len(unique), override_color=override_color,
        mapped_colors=[dict(c64_index=i, c64_color=c64_color_name(i), texels=int(n))
                                                     for i, n in enumerate(histogram) if n])
    return SvgSurface(Mesh(name, vertices, faces, face_colors=colors), bindings, report,
                      c64_color_name(int(np.argmax(histogram))), depth == 0)


def load_svg_surface(path, name, *, depth=5.0, resolution=512, alpha_threshold=128,
                     keep_background=True, texture_path=None, outlines_only=False,
                     override_color=None):
    rgba, report = bake_svg(path, resolution=resolution, keep_background=keep_background,
                            outlines_only=outlines_only)
    result = surface_from_rgba(rgba, name, depth=depth, alpha_threshold=alpha_threshold,
                               texture_path=texture_path, report=report, override_color=override_color)
    for warning in result.report['warnings']:
        print('SVG: ' + warning, flush=True)
    print(f'SVG fill: {len(result.mesh.faces)} faces, {result.report["opaque_texels"]} painted texels at {resolution}px', flush=True)
    return result
