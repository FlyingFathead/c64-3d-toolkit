"""GMod3-owned validation of the current V3 artwork and UI switches."""
from pathlib import Path


def normalize(a):
    from . import cli
    from .input_flip import options as flip_options
    if getattr(a,'viewport_width',None) is not None and not (a.blend or a.scene):
        raise ValueError('--viewport-width currently applies to --blend/--scene inputs')
    if any(flip_options(a).values()):
        print("Input artwork flip: "+", ".join(k.removeprefix("flip_") for k,v in flip_options(a).items() if v)+" (host conversion; HUD unchanged)",flush=True)
    if getattr(a,'hud_default',None) is not None:
        a.text_overlay=a.hud_default=='enabled'
    a.hud_visible=getattr(a,'text_overlay',True)
    explicit_toggle=getattr(a,'allow_hud_toggle',None)
    if explicit_toggle and (not a.interactive_cart or a.renderer not in ('hors-renderer-v3','hors-render-v3') or a.blend or a.scene):
        raise ValueError('--allow-hud-toggle requires a standalone HORS-V3/V4 GMod3 interactive cart')
    a.hud_toggle_allowed=a.interactive_cart if explicit_toggle is None else explicit_toggle
    if any(getattr(a,key,None) is not None for key in ('exhibition_default','exhibition_order','exhibition_interval')):
        if not a.interactive_cart or a.renderer not in ('hors-renderer-v3','hors-render-v3') or a.blend or a.scene:
            raise ValueError('Exhibition options require a standalone HORS-V3/V4 GMod3 --interactive-cart')
    if getattr(a,'starfield_profile',None) is not None and (not a.interactive_cart or not a.include_starfield or a.renderer not in ('hors-renderer-v3','hors-render-v3') or a.blend or a.scene):
        raise ValueError('--starfield-profile requires a standalone HORS-V3/V4 GMod3 interactive cart with included stars')
    if a.starfield_default is not None:
        a.background_effect = 'starfield-forward' if a.starfield_default == 'enabled' else 'none'
    if not a.include_starfield and a.background_effect != 'none':
        raise ValueError('--no-starfield cannot be combined with an enabled starfield')
    if (a.starfield_default is not None or not a.include_starfield) and (a.renderer not in ('hors-renderer-v3','hors-render-v3') or a.blend or a.scene):
        raise ValueError('Starfield inclusion/default switches require a standalone HORS-V3/V4 GMod3 build')
    source = cli._selected_source_path(a)
    is_svg = source is not None and source.suffix.lower() == '.svg'
    if a.max_fit_scale is None:
        a.max_fit_scale = 1000.0 if is_svg else 1.4
    svg_switches = (a.svg_outlines_only or a.svg_no_colors or a.svg_override_with_color is not None)
    if svg_switches and (not is_svg or a.renderer not in ('hors-renderer-v3', 'hors-render-v3')):
        raise ValueError('SVG colour/outline switches require an SVG source and HORS-V3/V4 GMod3')
    if a.svg_no_colors and a.svg_override_with_color is not None:
        raise ValueError('--svg-no-colors and --svg-override-with-color are mutually exclusive')
    if a.svg_presentation_modes and (not is_svg or not a.interactive_cart or a.surface_encoding != 'native'):
        raise ValueError('--svg-presentation-modes requires an interactive SVG and native colour encoding')
    if (a.svg_background_card or a.svg_outline_variant) and not a.svg_presentation_modes:
        raise ValueError('SVG presentation variants require --svg-presentation-modes')
    fill_style = getattr(a, 'fill_style', None)
    if fill_style:
        selected = {'wireframe':'none', 'solid':'material', 'gradient':'gradient',
                    'textured':'textured', 'metallic':'metallic'}[fill_style]
        if a.surface_fill is not None and a.surface_fill != selected:
            raise ValueError('--fill-style and --surface-fill select different styles')
        a.surface_fill = selected
    if getattr(a, 'surface_fill', None) is None:
        source = cli._selected_source_path(a)
        a.surface_fill = 'material' if source and source.suffix.lower() == '.svg' and a.renderer in ('hors-renderer-v3', 'hors-render-v3') else 'none'
    if svg_switches and a.surface_fill == 'none':
        raise ValueError('SVG colour/outline switches use painted contours; omit --fill-style wireframe')
    if a.svg_no_colors:
        a.surface_fill = 'material'
        a.color, a.background_color, a.border_color = 'white', 'black', 'black'
        a.ignore_colors = True
        a.include_starfield = False
        if a.svg_presentation_modes or a.background_effect != 'none':
            raise ValueError('--svg-no-colors requires a plain diagnostic build without presentation modes or background effects')
    elif a.svg_override_with_color is not None:
        # A literal override is solid unless a gradient was explicitly asked for.
        if not fill_style and a.surface_fill == 'gradient':
            a.surface_fill = 'material'
    if a.svg_presentation_modes and (a.surface_fill not in ('gradient', 'material') or svg_switches):
        raise ValueError('--svg-presentation-modes requires original solid/gradient SVG colours')
    if getattr(a, 'surface_texture', None):
        source = cli._selected_source_path(a)
        if not source or source.suffix.lower() != '.svg' or a.surface_fill != 'textured':
            raise ValueError('--surface-texture requires an SVG source and --surface-fill textured')
    if getattr(a, 'background_effect', 'none') != 'none' and (a.renderer not in ('hors-renderer-v3','hors-render-v3') or a.blend or a.scene):
        raise ValueError('--background-effect requires a standalone HORS-V3/V4 GMod3 build')
