"""Public renderer names and stable implementation identifiers."""
ALIASES = {'hors-render-v1': 'yunroll-cart-v10', 'hors-render-v1-scene': 'yunroll-cart-v10-scene'}
ALIASES.update({'hors-render-v2-beta1': 'yunroll-cart-v10-scene', 'hors-render-v2-beta1-scene': 'yunroll-cart-v10-scene'})
ALIASES.update({'hors-render-v2': 'yunroll-cart-v10', 'hors-render-v2-scene': 'yunroll-cart-v10-scene'})
DEFAULT_RENDERER = 'hors-renderer-v3'
def implementation(name):
    return ALIASES.get(name, name)
def public_name(name):
    return {'yunroll-cart-v10': 'hors-render-v1', 'yunroll-cart-v10-scene': 'hors-render-v1-scene'}.get(name, name)
