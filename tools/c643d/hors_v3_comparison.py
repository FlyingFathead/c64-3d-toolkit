"""V3 pipeline in the preserved external PLAY ALL comparison wrapper.

The menu stays V2 by default. Only explicit comparison jobs use these callbacks;
old menu sources, picture references and assembly implementations are retained.
"""
from dataclasses import replace
from pathlib import Path
from . import hors_v2_stable as v2
from .hors_v3 import encoding_plan, patch_literal_runtime


def prepare_menu(root,renderer,tass,tass_args=(),sources=None,prefer='fps',
                 work_prefix='comparison-hors-v3',prepare=None,**unused):
    from . import cartuniform
    prepare=prepare or cartuniform.prepare
    if sources is None:sources=cartuniform.demos(root)
    plans={};encoders={}
    def frames(demo):
        rows,encode,policy,literal,runs,palette=encoding_plan(demo.frames,demo.colors,demo.screen,3,2048,'literal')
        assert literal or not demo.colors
        plans[demo.name]=(policy,runs)
        encoders[demo.name]=encode
        return replace(demo,frames=rows)
    def runtime(source,demo):
        return patch_literal_runtime(source,plans[demo.name][1]) if demo.colors else source
    with v2.staged(root) as stage:
        entries,image,info,used,first_free=prepare(stage,'yunroll-cart-v10',tass,tass_args,
            sources=sources,prefer=prefer,work_prefix=work_prefix,frame_encoders=encoders,
            frame_pipeline=frames,runtime_pipeline=runtime)
        for entry in info:
            entry.update(renderer='hors-renderer-v3',wire_format='hors-v3-literal-colours',
                         encoding_choice={'gap':3,'batch_budget':2048},v3_color_plan=plans[entry['name']][0])
        v2.save_builds(stage,root)
        entries=[(name,Path(root)/path.relative_to(stage)) for name,path in entries]
    return entries,image,info,used,first_free
