"""Named metallic lighting ramps and user-defined native VIC-II colour stops."""
from .colors import c64_color_index

# Silhouette black followed by shadow, midtone, light and highlight.
# The original four ramps retain their exact indices and lighting thresholds.
SHADE_PALETTES = {
    'grey': (0, 11, 12, 15, 1),
    'blue': (0, 6, 14, 3, 1),
    'red': (0, 9, 2, 10, 1),
    'green': (0, 11, 5, 13, 1),
    'cyan': (0, 6, 14, 3, 1),
    'purple': (0, 6, 4, 10, 1),
    'yellow': (0, 9, 8, 7, 1),
    'orange': (0, 9, 8, 7, 1),
    'brown': (0, 9, 9, 8, 7),
    'light_red': (0, 2, 10, 15, 1),
    'light_green': (0, 5, 13, 7, 1),
    'light_blue': (0, 6, 14, 3, 1),
    'black': (0, 11, 11, 12, 15),
    'white': (0, 12, 15, 1, 1),
    'dark_gray': (0, 11, 11, 12, 15),
    'light_gray': (0, 12, 15, 1, 1),
}


def palette_name(value):
    name = value.lower().strip().replace('-', '_').replace(' ', '_')
    return {'metallic': 'grey', 'gray': 'grey', 'dark_grey': 'dark_gray',
            'light_grey': 'light_gray', 'magenta': 'purple', 'pink': 'light_red',
            'gold': 'yellow', 'silver': 'grey', 'aqua': 'cyan'}.get(name, name)


def parse_ramp(value):
    """Accept 2..16 ordered shade stops; black background is implicit."""
    from argparse import ArgumentTypeError
    try:
        parts = value.split(',')
        if not 2 <= len(parts) <= 16 or any(not p.strip() for p in parts):
            raise ValueError('use 2..16 comma-separated colour names or indices, dark to light')
        return tuple(c64_color_index(p.strip()) for p in parts)
    except ValueError as exc:
        raise ArgumentTypeError(f'--surface-ramp: {exc}') from exc


def shade_codes(palette='grey', ramp=None):
    if ramp is None:
        try:
            return SHADE_PALETTES[palette_name(palette)]
        except KeyError as exc:
            raise ValueError(f'Unknown surface shade palette: {palette}') from exc
    if not 2 <= len(ramp) <= 16 or any(not isinstance(c, int) or not 0 <= c <= 15 for c in ramp):
        raise ValueError('Surface ramp requires 2..16 native colour indices')
    return (0, *ramp)
