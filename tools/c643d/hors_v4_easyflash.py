"""HORS-V4's EasyFlash choice, using the preserved V3 build implementation."""
from copy import copy
import json
from pathlib import Path
from .renderer_labels import label_new_easyflash


def build(args):
    from . import cli
    core=copy(args);core.renderer='hors-renderer-v3';core.requested_renderer=core.renderer
    core.run=False
    if not core.output:
        source=core.blend or core.scene or core.obj or core.svg or core.object or core.shape
        core.output=Path(source or 'object').stem+'-hors-v4-ef'
    core.output=core.output.removesuffix('.crt')
    result=cli.cmd_build(core)
    if result or core.no_assemble:return result
    out=Path(core.output_dir).resolve() if core.output_dir else cli.BUILD
    crt=out/(core.output+'.crt');path=out/(core.output+'-manifest.json')
    meta=json.loads(path.read_text())
    if meta.get('build_screen'):
        evidence=label_new_easyflash(crt,'hors-v4-ef')
    else:
        import hashlib
        digest=hashlib.sha256(crt.read_bytes()).hexdigest()
        evidence=dict(original_crt_sha256=digest,crt_sha256=digest,bytes=0,
            change='no standard startup renderer field; preserved authored-scene image')
    meta.update(renderer='hors-renderer-v4',renderer_label='hors-v4-ef',
        renderer_implementation='hors-renderer-v3',cartridge='EasyFlash',renderer_label_update=evidence)
    if meta.get('build_screen'):meta['build_screen']['renderer']='hors-v4-ef'
    path.write_text(json.dumps(meta,indent=2)+'\n')
    print('Renderer: hors-v4-ef | cartridge: EasyFlash | implementation: preserved hors-v3',flush=True)
    if args.run:
        vice=cli.resolve_executable(args.vice,'vice')
        if not vice:raise ValueError('VICE not found')
        return cli.run_cartridge(vice,crt,args.vice_args,clean_settings=args.vice_clean_settings,cwd=cli.ROOT)
    return 0
