"""Public renderer names and stable implementation identifiers."""
ALIASES = {'hors-render-v1': 'yunroll-cart-v10', 'hors-render-v1-scene': 'yunroll-cart-v10-scene'}
def implementation(name):
    return ALIASES.get(name, name)
def public_name(name):
    return {'yunroll-cart-v10': 'hors-render-v1', 'yunroll-cart-v10-scene': 'hors-render-v1-scene'}.get(name, name)
