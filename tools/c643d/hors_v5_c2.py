"""HORS-V5 candidate 2: bounded clearing with per-animation colour encoding.

Only transport and screen-write instructions change. Geometry, palette mapping
and colour-overlap decisions are the existing pipeline's exact output.
"""
from contextlib import contextmanager
from copy import copy
import hashlib
import json
from pathlib import Path

from . import hors_v2_stable as v2, hors_v3 as v3, hors_v5 as c1
from .optimize import picture_bytes

NAME = 'hors-renderer-v5-c2'


def prepare_clears(frames, encode, colors, *, shared_bytes=None):
    prepared=[]
    for frame in frames:
        if shared_bytes is None:
            if colors and len(frame.color_spans)>255:
                raise ValueError('C2 runs colour span count exceeds 255')
            other=1+(1+4*len(frame.color_spans) if colors else 0)
        else:
            other=1+shared_bytes
        chosen=c1.plan_clear(frame,min(255,(1024-other)//3))
        block,metadata=encode(chosen,colors)
        if metadata>1024 or len(block)>8192:
            raise ValueError('C2 frame exceeds metadata or 8 KiB bank capacity')
        prepared.append(chosen)
    return prepared


def cost(frames, encode, colors, mode, policy, runs):
    """CPU heuristic, not a measured FPS claim; runtime profiles remain decisive."""
    score=0
    for frame in frames:
        _,metadata=encode(frame,colors)
        score+=c1.clear_cost(frame.clear_spans)+13*metadata
        if not colors:continue
        if mode=='runs':
            score+=190*len(frame.color_spans)+22*sum(s[2] for s in frame.color_spans)
        elif policy.get('color_bytes_per_frame') is not None:
            score+=19*policy['dynamic_screen_cells']+50*len(runs)
        else:
            score+=100*len(frame.color_spans)+11*sum(s[2] for s in frame.color_spans)
    return score


def encoding_plan(frames, colors=True, base=0x10, draw_gap=6, batch_budget=2048,
                  color_encoding='literal', *, mode='auto', shared_plan=None):
    if mode not in ('auto','runs','shared'):raise ValueError('C2 colour plan must be auto, runs or shared')
    if color_encoding!='literal':raise ValueError('C2 currently requires literal colour encoding')
    shared_plan=shared_plan or v3.encoding_plan
    candidates=[];failures={}
    for choice in (('runs','shared') if colors else ('runs',)):
        if mode!='auto' and choice!=mode and colors:continue
        try:
            if choice=='runs':
                encode=v2.encoder(draw_gap,batch_budget)
                fs=prepare_clears(frames,encode,colors)
                policy=dict(old_color_reset_removed=False,previous_picture_dependency=False,
                            color_encoding='per-picture colour runs',clear_plan='hors-v5-c2-bounded-clears')
                literal=False;runs=[];palette=None
            else:
                fs,encode,policy,literal,runs,palette=shared_plan(frames,colors,base,draw_gap,batch_budget,color_encoding)
                fs=prepare_clears(fs,encode,colors,shared_bytes=policy.get('color_bytes_per_frame') if literal else None)
                policy=dict(policy,clear_plan='hors-v5-c2-bounded-clears')
            for before,after in zip(frames,fs,strict=True):
                if picture_bytes(before,base)!=picture_bytes(after,base):
                    raise AssertionError('C2 changed source bitmap or screen colours')
            score=cost(fs,encode,colors,choice,policy,runs)
            candidates.append((score,choice,fs,encode,policy,literal,runs,palette))
        except ValueError as exc:
            failures[choice]=str(exc)
    if not candidates:
        raise ValueError('C2 capacity: no colour plan fits; '+str(failures))
    score,choice,fs,encode,policy,literal,runs,palette=min(candidates,key=lambda item:(item[0],item[1]))
    policy=dict(policy,candidate='c2',c2_color_plan=choice,color_plan_requested=mode,
                selection='host CPU heuristic; verify with measured contest',
                estimated_plan_costs={item[1]:item[0] for item in candidates},unavailable_plans=failures)
    return fs,encode,policy,literal,runs,palette


@contextmanager
def installed(mode='auto'):
    """Reuse the V3 build frontend; keep V2 colour reset for run-encoded frames."""
    with v2._lock:
        old_plan,old_stage,old_patch=v3.encoding_plan,v2.staged,v3.patch_runtime
        selected={}
        def plan(*args,**kwargs):
            result=encoding_plan(*args,**kwargs,mode=mode,shared_plan=old_plan)
            selected['mode']=result[2]['c2_color_plan']
            return result
        def patch(source):
            return source if selected.get('mode')=='runs' else old_patch(source)
        @contextmanager
        def staged(*args,**kwargs):
            with old_stage(*args,**kwargs) as stage:
                suffix='-scene' if kwargs.get('scene') else ''
                runtime=stage/f'c64/renderer-yunroll-cart-v10{suffix}.asm'
                runtime.write_text(c1.patch_clear(runtime.read_text()))
                yield stage
        v3.encoding_plan,v2.staged,v3.patch_runtime=plan,staged,patch
        try:yield
        finally:v3.encoding_plan,v2.staged,v3.patch_runtime=old_plan,old_stage,old_patch


def describe_output(crt):
    from .renderer_labels import label_new_easyflash
    crt=Path(crt);path=crt.with_name(crt.stem+'-manifest.json');meta=json.loads(path.read_text())
    if meta.get('build_screen'):
        evidence=label_new_easyflash(crt,'hors-v5-c2');meta['build_screen']['renderer']='hors-v5-c2'
    else:
        digest=hashlib.sha256(crt.read_bytes()).hexdigest()
        evidence=dict(original_crt_sha256=digest,crt_sha256=digest,bytes=0,change='authored scene without startup renderer field')
    policy=meta['color_policy']
    meta.update(renderer=NAME,renderer_label='hors-v5-c2',candidate='c2',experimental=True,
        implementation='V5 clearing with selected V2 runs or V3 shared colour transport',
        wire_format='hors-v5-c2-'+policy['c2_color_plan'],cartridge='EasyFlash',renderer_label_update=evidence)
    path.write_text(json.dumps(meta,indent=2)+'\n');return meta


def build(args):
    from . import cli
    if getattr(args,'cart_type',None) not in (None,'easyflash'):raise ValueError('HORS-V5-c2 requires EasyFlash')
    # Run-based colour metadata does not implement the interactive recolouring hooks.
    if (args.interactive_cart or args.background_effect!='none'
            or getattr(args,'starfield_default',None)=='enabled'
            or getattr(args,'svg_presentation_modes',False)):
        raise ValueError('HORS-V5-c2 currently supports standalone objects and authored scenes without interactive effects')
    core=copy(args);core.renderer=core.requested_renderer='hors-renderer-v3';core.run=False
    if not core.output:
        source=core.blend or core.scene or core.obj or core.svg or core.object or core.shape
        core.output=Path(source or 'object').stem+'-hors-v5-c2'
    core.output=core.output.removesuffix('.crt')
    with installed(getattr(args,'v5_color_plan','auto')):result=cli.cmd_build(core)
    if result or core.no_assemble:return result
    out=Path(core.output_dir).resolve() if core.output_dir else cli.BUILD
    crt=out/(core.output+'.crt');meta=describe_output(crt)
    print('Renderer: hors-v5-c2 | cartridge: EasyFlash | colour transport: '+meta['color_policy']['c2_color_plan'],flush=True)
    if args.run:
        vice=cli.resolve_executable(args.vice,'vice')
        if not vice:raise ValueError('VICE not found')
        return cli.run_cartridge(vice,crt,args.vice_args,clean_settings=args.vice_clean_settings,cwd=cli.ROOT)
    return 0


def prepare_menu(root,renderer,tass,tass_args=(),sources=None,prefer='fps',prepare=None,**unused):
    """Common-controller comparison; each entry independently selects its plan."""
    from dataclasses import replace
    from . import cartuniform
    prepare=prepare or cartuniform.prepare
    sources=cartuniform.demos(root) if sources is None else sources
    plans={};encoders={}
    def frames(demo):
        result=encoding_plan(demo.frames,demo.colors,demo.screen,3,2048)
        fs,encode,policy,literal,runs,palette=result
        plans[demo.name]=result;encoders[demo.name]=encode
        return replace(demo,frames=fs)
    def runtime(source,demo):
        _,_,policy,literal,runs,palette=plans[demo.name]
        source=c1.patch_clear(source)
        if demo.colors and policy['c2_color_plan']=='shared':
            source=v3.patch_literal_runtime(source,runs,palette) if literal else v3.patch_runtime(source)
        return source
    with v2.staged(root) as stage:
        entries,image,info,used,first_free=prepare(stage,'yunroll-cart-v10',tass,tass_args,
            sources=sources,prefer=prefer,work_prefix='comparison-hors-v5-c2',frame_encoders=encoders,
            frame_pipeline=frames,runtime_pipeline=runtime)
        for entry in info:
            policy=plans[entry['name']][2]
            entry.update(renderer='hors-v5-c2',wire_format='hors-v5-c2-'+policy['c2_color_plan'],
                         encoding_choice=dict(gap=3,batch_budget=2048),v5_c2_color_plan=policy)
        v2.save_builds(stage,root)
        entries=[(name,Path(root)/path.relative_to(stage)) for name,path in entries]
    return entries,image,info,used,first_free
