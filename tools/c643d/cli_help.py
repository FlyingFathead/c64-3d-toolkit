"""Generate discoverable help from the actual parsers, without build imports."""
import argparse


class ToolkitParser(argparse.ArgumentParser):
    def format_help(self):
        from . import __version__
        text = f'c64-3d-toolkit v{__version__} | Harry Horsperg\n\n' + super().format_help()
        build = getattr(self, 'build_help_parser', None)
        if build is not None:
            text += '\nBUILD OPTIONS (also: c643d build --help)\n\n'
            text += build.format_help()
        return text


class FullHelp(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                for name, command in action.choices.items():
                    if name not in ('build', 'cart-stream', 'cartridge-demo'):
                        print('\nCOMMAND: ' + name + '\n')
                        command.print_help()
        parser.exit()


def group_build_options(parser):
    """Group the existing actions without changing parsing or duplicating flags."""
    groups={name:parser.add_argument_group(name) for name in (
        'Inputs and scene sampling','Projection and geometry','Materials and colours',
        'Playback and controls','Renderer and cartridge','Output and diagnostics','Tools and configuration')}
    options=parser._optionals
    for action in list(options._group_actions):
        dest=action.dest
        if dest=='help':continue
        if dest in ('config','no_config','tass','vice','blender','cartconv','tass_args','vice_args',
                    'no_tass_default_args','no_vice_default_args','vice_clean_settings','configure_blender_color_space'):
            name='Tools and configuration'
        elif dest in ('shape','object','obj','svg','blend','scene','frames','frame_start','frame_end','sample_step',
                      'blender_output_fps','blender_color_space'):
            name='Inputs and scene sampling'
        elif dest.startswith(('surface','svg_')) or dest in ('color','background_color','border_color','ignore_colors','fill_style','v3_color_encoding'):
            name='Materials and colours'
        elif dest.startswith(('renderer','cart_','gmod3_','v2_','v3_','v4_','v5_','v6_','v7_','v8_','v9_','v10_')) or dest in ('prefer','legacy_cart'):
            name='Renderer and cartridge'
        elif dest.startswith(('hud','text_overlay','star','include_star','interactive','exhibition','rotation','tempo')) or dest in ('frame_ticks','intro','ending','fps_lock','animation'):
            name='Playback and controls'
        elif dest in ('output','output_dir','name','run','no_assemble','overwrite_policy','ignore_warnings','rastertime_profiler'):
            name='Output and diagnostics'
        else:name='Projection and geometry'
        options._group_actions.remove(action)
        groups[name]._group_actions.append(action)
