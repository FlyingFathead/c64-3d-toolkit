"""Explicit material-number interpretation before the shared C64 palette mapper."""
import math
from .colors import nearest_c64_color_index


def material_rgb_bytes(rgb, color_space='linear'):
    if color_space not in ('linear','srgb'):
        raise ValueError('Blender colour space must be linear or srgb')
    values=tuple(float(v) for v in rgb[:3])
    if len(values)!=3 or not all(math.isfinite(v) for v in values):
        raise ValueError('Blender material RGB must contain three finite values')
    if color_space=='linear':
        values=tuple(12.92*max(0.,v) if v<=.0031308
                     else 1.055*max(0.,v)**(1/2.4)-.055 for v in values)
    return tuple(max(0,min(255,round(v*255))) for v in values)


def material_color_index(rgb, color_space='linear'):
    return nearest_c64_color_index(material_rgb_bytes(rgb,color_space))
