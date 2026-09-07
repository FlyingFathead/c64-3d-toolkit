"""Explicit V7 speed/RAM trade-off; never changes geometry or sample cadence."""


def apply_preference(source, renderer, prefer='fps'):
    if prefer not in ('fps', 'ram'):
        raise ValueError('--prefer must be fps or ram')
    if prefer == 'ram' and renderer not in ('yunroll-cart-v7', 'yunroll-cart-v7-scene'):
        raise ValueError('--prefer ram requires a V7 cartridge renderer')
    if renderer in ('yunroll-cart-v7', 'yunroll-cart-v7-scene'):
        marker = 'PREFER_RAM = 0'
        if marker not in source:
            raise ValueError('V7 source is missing its kernel preference marker')
        return source.replace(marker, f'PREFER_RAM = {int(prefer == "ram")}', 1)
    return source
