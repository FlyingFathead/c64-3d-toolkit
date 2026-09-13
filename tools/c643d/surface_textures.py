"""HORS-V3-only diffuse image maps; the legacy OBJ/MTL reader is unchanged."""
from dataclasses import dataclass
from pathlib import Path
import shlex
import numpy as np
from .colors import nearest_c64_color_index

@dataclass
class Texture:
    pixels: np.ndarray
    scale: tuple = (1.0, 1.0)
    offset: tuple = (0.0, 0.0)
    clamp: bool = False

    def sample(self, uv):
        coords = uv * np.array(self.scale) + np.array(self.offset)
        coords = np.clip(coords, 0, 1) if self.clamp else coords % 1.0
        h, w = self.pixels.shape
        x = np.minimum((coords[:, 0] * w).astype(int), w - 1)
        # OBJ v grows upwards; image rows grow downwards.
        y = h - 1 - np.minimum((coords[:, 1] * h).astype(int), h - 1)
        return self.pixels[y, x]


def _map_options(words):
    scale, offset, clamp, i = (1., 1.), (0., 0.), False, 0
    while i < len(words) and words[i].startswith('-'):
        option = words[i]; i += 1
        if option in ('-s', '-o'):
            values = []
            while i < len(words) and len(values) < 3:
                try: value = float(words[i])
                except ValueError: break
                values.append(value); i += 1
            if not values:
                raise ValueError(f'{option} requires numeric texture coordinates')
            default = 1. if option == '-s' else 0.
            values += [default] * (3 - len(values))
            if option == '-s': scale = tuple(values[:2])
            else: offset = tuple(values[:2])
        elif option == '-clamp':
            if i >= len(words) or words[i] not in ('on', 'off'):
                raise ValueError('-clamp requires on or off')
            clamp = words[i] == 'on'; i += 1
        else:
            raise ValueError(f'Unsupported map_Kd option {option}; bake it into the image first')
    if i == len(words): raise ValueError('map_Kd requires an image filename')
    return ' '.join(words[i:]), scale, offset, clamp


def _materials(path):
    values, active = {}, None
    for raw in path.read_text(encoding='utf-8', errors='replace').splitlines():
        words = shlex.split(raw, comments=True)
        if not words: continue
        key, args = words[0].lower(), words[1:]
        if key == 'newmtl':
            active = ' '.join(args)
            values[active] = dict(kd=(1., 1., 1.), opacity=1.)
        elif active is not None:
            entry = values[active]
            if key == 'kd':
                if len(args) != 3: raise ValueError('Textured Kd requires three RGB numbers')
                entry['kd'] = tuple(max(0., min(1., float(v))) for v in args)
            elif key == 'map_kd':
                ref, scale, offset, clamp = _map_options(args)
                entry['map'] = (path.parent / ref, scale, offset, clamp)
            elif key in ('d', 'tr'):
                entry['opacity'] = float(args[-1]) if key == 'd' else 1. - float(args[-1])
    return values


def load_textures(obj_path, mesh, *, report=None):
    """Return face/vertex UV bindings and palette-mapped texture images."""
    from PIL import Image
    obj_path = Path(obj_path)
    lines = obj_path.read_text(encoding='utf-8', errors='replace').splitlines()
    materials = {}
    for raw in lines:
        words = shlex.split(raw, comments=True)
        if words and words[0].lower() == 'mtllib':
            for ref in words[1:]: materials.update(_materials(obj_path.parent / ref))
    textures = {}
    for name, mat in materials.items():
        if 'map' not in mat: continue
        if mat['opacity'] != 1.:
            raise ValueError('HORS-V3 textures are opaque; transparency is not implemented')
        path, scale, offset, clamp = mat['map']
        with Image.open(path) as image:
            rgba = np.array(image.convert('RGBA'))
        if np.any(rgba[:, :, 3] != 255):
            raise ValueError(f'{path}: transparent image pixels are unsupported')
        rgb = np.rint(rgba[:, :, :3] * np.array(mat['kd'])).astype(np.uint8)
        unique, inverse = np.unique(rgb.reshape(-1, 3), axis=0, return_inverse=True)
        mapped = np.array([nearest_c64_color_index(tuple(map(int, c))) for c in unique], dtype=np.uint8)
        pixels = mapped[inverse].reshape(rgb.shape[:2])
        textures[name] = Texture(pixels, scale, offset, clamp)
        if report is not None:
            from .colors import c64_color_name
            histogram = np.bincount(pixels.ravel(), minlength=16)
            report[name] = dict(source_rgb_colors=len(unique), width=pixels.shape[1],
                height=pixels.shape[0], kd=list(mat['kd']),
                mapped_colors=[dict(c64_index=i, c64_color=c64_color_name(i), pixels=int(n))
                               for i, n in enumerate(histogram) if n])
    uvs, faces, active, vertex_count = [], [], None, 0
    for raw in lines:
        words = shlex.split(raw, comments=True)
        if not words: continue
        if words[0] == 'v': vertex_count += 1
        elif words[0] == 'vt':
            uvs.append((float(words[1]), float(words[2]) if len(words) > 2 else 0.))
        elif words[0] == 'usemtl': active = ' '.join(words[1:])
        elif words[0] == 'f':
            corners = []
            for token in words[1:]:
                parts = token.split('/')
                v = int(parts[0]); v = vertex_count + v if v < 0 else v - 1
                uv = None
                if len(parts) > 1 and parts[1]:
                    t = int(parts[1]); t = len(uvs) + t if t < 0 else t - 1
                    if not 0 <= t < len(uvs): raise ValueError('Texture coordinate index out of range')
                    uv = uvs[t]
                if not corners or corners[-1][0] != v: corners.append((v, uv))
            if len(corners) >= 3 and corners[0][0] == corners[-1][0]: corners.pop()
            if len({v for v, uv in corners}) < 3: continue
            if len({v for v, uv in corners}) != len(corners):
                raise ValueError('Textured faces cannot repeat a vertex with ambiguous UVs')
            faces.append((active, dict(corners)))
    if len(faces) != len(mesh.faces): raise ValueError('Texture face order differs from geometry')
    result = []
    used_maps = 0
    for face, (material, corners) in zip(mesh.faces, faces):
        if set(face) != set(corners): raise ValueError('Texture vertex binding differs from geometry')
        texture = textures.get(material)
        if texture is not None:
            if any(corners[v] is None for v in face):
                raise ValueError(f'Material {material} has map_Kd but its face is missing OBJ vt coordinates')
            used_maps += 1
        result.append((texture, corners))
    if not used_maps:
        raise ValueError('--surface-fill textured needs a used map_Kd image and OBJ vt coordinates; use material for plain Kd colours')
    return result


def paint(picture, owners, points, triangles, bindings):
    """Perspective-correct UV interpolation for visible triangle pixels only."""
    flat_owner = owners.ravel()
    visible = np.flatnonzero(flat_owner >= 0)
    if len(visible) == 0:
        return
    order = np.argsort(flat_owner[visible], kind='stable')
    visible = visible[order]
    ids = flat_owner[visible]
    starts = np.r_[0, np.flatnonzero(np.diff(ids)) + 1, len(ids)]
    for start, end in zip(starts[:-1], starts[1:]):
        ti = int(ids[start])
        face, a, b, c = triangles[ti]
        texture, uv_map = bindings[face]
        if texture is None: continue
        where = visible[start:end]
        py, px = np.divmod(where, 256)
        x, y = px + .5, py + .5
        x0,y0,q0 = points[a]; x1,y1,q1 = points[b]; x2,y2,q2 = points[c]
        den = (y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        w0 = ((y1-y2)*(x-x2)+(x2-x1)*(y-y2)) / den
        w1 = ((y2-y0)*(x-x2)+(x0-x2)*(y-y2)) / den
        weights = np.column_stack((w0*q0, w1*q1, (1-w0-w1)*q2))
        uv = weights @ np.array([uv_map[a], uv_map[b], uv_map[c]]) / weights.sum(axis=1)[:,None]
        picture[py, px] = texture.sample(uv)
