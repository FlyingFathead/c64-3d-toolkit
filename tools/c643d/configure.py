"""Small, dependency-free configuration actions with comment-preserving writes."""
import configparser
import os
from pathlib import Path
import re
import tempfile


def save_blender_color_space(path, value):
    if value not in ('linear','srgb'):
        raise ValueError('Blender colour space must be linear or srgb')
    path=Path(path).expanduser()
    text=path.read_text(encoding='utf-8') if path.exists() else ''
    config=configparser.ConfigParser(interpolation=None)
    config.read_string(text)
    lines=text.splitlines(keepends=True)
    section=None; start=None; end=len(lines); found=False
    for i,line in enumerate(lines):
        match=re.match(r'^\s*\[([^]]+)\]',line)
        if match:
            if section=='render_defaults':
                end=i;break
            section=match.group(1)
            if section=='render_defaults':start=i
        elif section=='render_defaults' and re.match(r'^\s*blender_color_space\s*[:=]',line,re.I):
            lines[i]=f'blender_color_space = {value}\n';found=True
    if not found:
        if start is None:
            if lines and not lines[-1].endswith('\n'):lines[-1]+='\n'
            lines.extend(['\n[render_defaults]\n',f'blender_color_space = {value}\n'])
        else:
            if end and not lines[end-1].endswith('\n'):lines[end-1]+='\n'
            lines.insert(end,f'blender_color_space = {value}\n')
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,temporary=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='') as handle:
            handle.write(''.join(lines));handle.flush();os.fsync(handle.fileno())
        if path.exists():os.chmod(temporary,path.stat().st_mode & 0o777)
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)
    return path


def configure_blender_color_space(path, value, current='linear', *, input_fn=None):
    if path is None:
        raise ValueError('Configuration writing cannot be combined with --no-config')
    if value=='ask':
        print('Blender material colour interpretation:')
        print('  1) linear: standard Blender material values; convert to sRGB (default)')
        print('  2) srgb: imported material numbers already represent sRGB; use directly')
        try:
            answer=(input_fn or input)(f'Select 1/2 or linear/srgb [{current}]: ').strip().lower()
        except EOFError as exc:
            raise ValueError('No selection received; use --configure-blender-color-space linear or srgb') from exc
        value={'1':'linear','2':'srgb','':current}.get(answer,answer)
    target=save_blender_color_space(path,value)
    print(f'Saved Blender colour space: {value} ({target})')
    return 0
