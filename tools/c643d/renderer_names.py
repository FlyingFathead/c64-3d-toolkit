"""Public renderer names and stable implementation identifiers."""
ALIASES = {'hors-render-v1': 'yunroll-cart-v10', 'hors-render-v1-scene': 'yunroll-cart-v10-scene'}
ALIASES.update({'hors-render-v2-beta1': 'yunroll-cart-v10-scene', 'hors-render-v2-beta1-scene': 'yunroll-cart-v10-scene'})
ALIASES.update({'hors-render-v2': 'yunroll-cart-v10', 'hors-render-v2-scene': 'yunroll-cart-v10-scene'})
DEFAULT_RENDERER = 'hors-v4'
def implementation(name):
    return ALIASES.get(name, name)
def public_name(name):
    return {'yunroll-cart-v10': 'hors-render-v1', 'yunroll-cart-v10-scene': 'hors-render-v1-scene'}.get(name, name)

# Short public selectors normalize before any preserved backend is entered.
SHORT_ALIASES = {
    'hors-v1':'hors-render-v1', 'hors-renderer-v1':'hors-render-v1',
    'hors-v1-scene':'hors-render-v1-scene', 'hors-renderer-v1-scene':'hors-render-v1-scene',
    'hors-v2':'hors-render-v2', 'hors-renderer-v2':'hors-render-v2',
    'hors-v2-scene':'hors-render-v2-scene', 'hors-renderer-v2-scene':'hors-render-v2-scene',
    'hors-v3':'hors-renderer-v3', 'hors-render-v3':'hors-renderer-v3',
    'hors-v4':'hors-renderer-v4', 'hors-render-v4':'hors-renderer-v4',
    'hors-v4-gmod3':'hors-renderer-v4', 'hors-v4-ef':'hors-renderer-v4',
}


def canonical_selector(name):
    return SHORT_ALIASES.get(name, name)


def selector_cartridge(name):
    return {'hors-v4-gmod3':'gmod3', 'hors-v4-ef':'easyflash'}.get(name)


def display_name(name, cartridge=None):
    name=canonical_selector(name)
    if name=='hors-renderer-v4':
        return 'hors-v4-'+('ef' if cartridge=='easyflash' else 'gmod3')
    if name=='hors-renderer-v3':
        return 'hors-v3'+('-gmod3' if cartridge=='gmod3' else '')
    for old,new in [('hors-render-v1','hors-v1'),('hors-render-v2','hors-v2')]:
        if name.startswith(old):return new+name[len(old):]
    return name
