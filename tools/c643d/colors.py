from __future__ import annotations

"""Host-side source-colour parsing and VIC-II palette mapping.

RGB/CSS/MTL work deliberately stops here.  Generated C64 tables contain only
native four-bit VIC-II colour indices (or ready-to-store hires screen bytes),
so the 6510 never searches a palette or performs colour-distance arithmetic.
"""

from functools import lru_cache
import math
import re


# A pragmatic Pepto-ish palette. Exact analogue output varies by machine and
# display chain, but these values provide a stable import mapping.
C64_PALETTE: dict[str, tuple[int, tuple[int, int, int]]] = {
    'black':       (0,  (0, 0, 0)),
    'white':       (1,  (255, 255, 255)),
    'red':         (2,  (136, 0, 0)),
    'cyan':        (3,  (170, 255, 238)),
    'purple':      (4,  (204, 68, 204)),
    'green':       (5,  (0, 204, 85)),
    'blue':        (6,  (0, 0, 170)),
    'yellow':      (7,  (238, 238, 119)),
    'orange':      (8,  (221, 136, 85)),
    'brown':       (9,  (102, 68, 0)),
    'light_red':   (10, (255, 119, 119)),
    'dark_gray':   (11, (51, 51, 51)),
    'gray':        (12, (119, 119, 119)),
    'light_green': (13, (170, 255, 102)),
    'light_blue':  (14, (0, 136, 255)),
    'light_gray':  (15, (187, 187, 187)),
}

_COLOR_NAMES = {
    'black':'#000000', 'silver':'#c0c0c0', 'gray':'#808080',
    'grey':'#808080', 'white':'#ffffff', 'maroon':'#800000',
    'red':'#ff0000', 'purple':'#800080', 'fuchsia':'#ff00ff',
    'magenta':'#ff00ff', 'green':'#008000', 'lime':'#00ff00',
    'olive':'#808000', 'yellow':'#ffff00', 'navy':'#000080',
    'blue':'#0000ff', 'teal':'#008080', 'aqua':'#00ffff',
    'cyan':'#00ffff', 'orange':'#ffa500', 'brown':'#a52a2a',
}


def c64_color_index(value: str | int | None) -> int:
    if value is None:
        return C64_PALETTE['white'][0]
    if isinstance(value, int):
        if 0 <= value <= 15:
            return value
        raise ValueError('C64 colour index must be 0..15')
    s=str(value).strip().lower().replace('-','_').replace(' ','_')
    if s.isdigit():
        n=int(s)
        if 0 <= n <= 15:
            return n
    aliases={
        'grey':'gray', 'dark_grey':'dark_gray', 'light_grey':'light_gray',
        'lightred':'light_red', 'lightgreen':'light_green',
        'lightblue':'light_blue',
    }
    s=aliases.get(s,s)
    if s not in C64_PALETTE:
        raise ValueError(f'unknown C64 colour {value!r}; use a palette name or 0..15')
    return C64_PALETTE[s][0]


def c64_color_name(index: int) -> str:
    for name,(n,_rgb) in C64_PALETTE.items():
        if n == index:
            return name
    raise ValueError(index)


def parse_source_color(value: str | None) -> tuple[int,int,int] | None:
    """Parse the common solid CSS colours useful to the SVG importer."""
    if not value:
        return None
    s=value.strip().lower()
    if s in ('none','transparent','currentcolor','inherit'):
        return None
    s=_COLOR_NAMES.get(s,s)
    if s.startswith('#'):
        h=s[1:]
        if len(h) in (3,4):
            h=''.join(ch*2 for ch in h)
        if len(h) in (6,8):
            try:
                rgb=tuple(int(h[i:i+2],16) for i in (0,2,4))
                if len(h)==8 and int(h[6:8],16)==0:
                    return None
                return rgb
            except ValueError:
                return None
    m=re.fullmatch(
        r'rgba?\(\s*([-+\d.]+)%?\s*[, ]\s*([-+\d.]+)%?\s*[, ]\s*([-+\d.]+)%?'
        r'(?:\s*[,/]\s*([-+\d.]+)%?)?\s*\)',s)
    if m:
        if m.group(4) is not None:
            alpha=float(m.group(4))
            if '%' in s[s.rfind(m.group(4)):]:
                alpha/=100.0
            if alpha<=0:
                return None
        pct='%' in s[:s.find(')')].split('/')[0]
        vals=[]
        for x in m.groups()[:3]:
            v=float(x)
            vals.append(round(v*2.55) if pct else round(v))
        return tuple(max(0,min(255,v)) for v in vals)
    return None


def _srgb_linear(v: int) -> float:
    c=v/255.0
    return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4


@lru_cache(maxsize=128)
def _lab(rgb: tuple[int,int,int]) -> tuple[float,float,float]:
    r,g,b=(_srgb_linear(v) for v in rgb)
    x=(0.4124564*r+0.3575761*g+0.1804375*b)/0.95047
    y=0.2126729*r+0.7151522*g+0.0721750*b
    z=(0.0193339*r+0.1191920*g+0.9503041*b)/1.08883
    delta=6.0/29.0
    def f(t:float)->float:
        return t**(1.0/3.0) if t>delta**3 else t/(3*delta*delta)+4.0/29.0
    fx,fy,fz=f(x),f(y),f(z)
    return 116*fy-16,500*(fx-fy),200*(fy-fz)


def nearest_c64_color_index(rgb: tuple[int,int,int]) -> int:
    """Map source RGB to a hue-preserving perceptual C64 palette match.

    C64's coarse palette has no dark green.  Giving CIELAB lightness half the
    weight of chroma/hue avoids turning dark green source materials brown or
    gray merely because those entries happen to have closer luminance.
    """
    rgb=tuple(max(0,min(255,int(v))) for v in rgb)
    l,a,b=_lab(rgb)
    best_index=1; best_distance=math.inf
    for _name,(index,palette_rgb) in C64_PALETTE.items():
        pl,pa,pb=_lab(palette_rgb)
        distance=0.5*(l-pl)**2+(a-pa)**2+(b-pb)**2
        if distance<best_distance:
            best_index=index; best_distance=distance
    return best_index


def nearest_c64_color(rgb: tuple[int,int,int]) -> str:
    return c64_color_name(nearest_c64_color_index(rgb))


def hires_screen_byte(foreground: int, background: int=0) -> int:
    """Return the VIC-II hires screen-RAM byte for two native colour nibbles."""
    if not 0<=foreground<=15 or not 0<=background<=15:
        raise ValueError('VIC-II colour indices must be 0..15')
    return (foreground<<4)|background
