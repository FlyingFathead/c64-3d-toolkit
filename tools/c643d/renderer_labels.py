"""Short labels for newly built cartridges, without changing rendering code."""
from .buildscreen import screen_codes
from .emit import bytes_lines


def padded_label(short, old='hors-renderer-v3'):
    if len(short)>len(old):raise ValueError('Renderer label exceeds the reserved title field')
    # The old field starts at floor((40-width)/2); place the short text at its
    # own centered column while preserving the field width and all addresses.
    left=(40-len(short))//2-(40-len(old))//2
    return ' '*left+short+' '*(len(old)-left-len(short))


def short_intro(source, short):
    old='\n'.join(bytes_lines(screen_codes('hors-renderer-v3')))
    new='\n'.join(bytes_lines(screen_codes(padded_label(short))))
    target='build_screen_text_renderer:\n'+old
    if source.count(target)!=1:raise ValueError('Expected one renderer title field')
    return source.replace(target,'build_screen_text_renderer:\n'+new,1)


def label_new_easyflash(crt, short):
    """Replace only the fixed-width startup text in this newly generated CRT.

    The preserved EasyFlash assembler produces the image first. No mapper,
    header, drawing code, addresses or picture data are modified here.
    """
    import hashlib
    from pathlib import Path
    path=Path(crt);data=path.read_bytes();old=bytes(screen_codes('hors-renderer-v3'))
    if data[:16]!=b'C64 CARTRIDGE   ' or int.from_bytes(data[22:24],'big')!=32:
        raise ValueError('Short EasyFlash label requires a standard type-32 CRT')
    if data.count(old)!=1:raise ValueError('Expected one V3 startup text field in new EasyFlash output')
    offset=data.index(old);replacement=bytes(screen_codes(padded_label(short)))
    changed=data[:offset]+replacement+data[offset+len(old):]
    path.write_bytes(changed)
    return dict(original_crt_sha256=hashlib.sha256(data).hexdigest(),
        crt_sha256=hashlib.sha256(changed).hexdigest(),offset=offset,bytes=len(old),
        change='fixed-width startup renderer text only; same instruction/data addresses')
