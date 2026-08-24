from __future__ import annotations
import math
from dataclasses import dataclass
from .mesh import Mesh, face_center, face_normal, rotate_xyz, dot

W,H=256,144
Z_TOL=0.0008

@dataclass
class Camera:
    distance: float = 110.0
    focal: float = 180.0
    cx: float = 128.0
    cy: float = 72.0

@dataclass
class FrameBuild:
    records: list[tuple[int,...]]
    clear_spans: list[tuple[int,int,int]]
    raw_pixels: int
    unique_pixels: int
    dda_mismatches: list[int]


def raster_triangle(zbuf, owner, face_index, p0, p1, p2):
    x0,y0,q0=p0; x1,y1,q1=p1; x2,y2,q2=p2
    den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
    if abs(den)<1e-12: return
    minx=max(0,math.floor(min(x0,x1,x2))); maxx=min(W-1,math.ceil(max(x0,x1,x2)))
    miny=max(0,math.floor(min(y0,y1,y2))); maxy=min(H-1,math.ceil(max(y0,y1,y2)))
    for y in range(miny,maxy+1):
        py=y+0.5; row=y*W
        for x in range(minx,maxx+1):
            px=x+0.5
            w0=((y1-y2)*(px-x2)+(x2-x1)*(py-y2))/den
            w1=((y2-y0)*(px-x2)+(x0-x2)*(py-y2))/den
            w2=1.0-w0-w1
            if w0>=-1e-8 and w1>=-1e-8 and w2>=-1e-8:
                q=w0*q0+w1*q1+w2*q2
                i=row+x
                if q>zbuf[i]:
                    zbuf[i]=q
                    owner[i]=face_index


def target_minor_steps(major:int,minor:int):
    if major<=0:return []
    out=[]; pos=0; half=major//2
    for i in range(major):
        new=((i+1)*minor+half)//major
        out.append(new>pos); pos=new
    assert pos==minor
    return out


def choose_dda(major:int,minor:int):
    if major==0 or minor==0:return 0,0,0
    target=target_minor_steps(major,minor)
    ratio=256.0*minor/major
    q0=int(math.floor(ratio))
    best=None
    for slope in range(max(1,q0-3),min(255,int(math.ceil(ratio))+3)+1):
        for phase in range(256):
            err=phase; got=[]; carries=0
            for _ in range(major):
                total=err+slope; carry=total>=256; err=total&255
                got.append(carry); carries+=int(carry)
            if carries!=minor:continue
            mismatch=sum(a!=b for a,b in zip(got,target))
            if best is None or mismatch<best[0]:
                best=(mismatch,slope,phase)
                if mismatch==0:return best
    if best is None: raise RuntimeError(f'no DDA for {major}/{minor}')
    return best


def oriented_dda(x0:int,y0:int,x1:int,y1:int):
    dx=abs(x1-x0); dy=abs(y1-y0)
    if dx>=dy:
        axis=0
        if x1<x0: x0,x1,y0,y1=x1,x0,y1,y0
        major=x1-x0; minor=abs(y1-y0); negative=y1<y0
    else:
        axis=1
        if y1<y0: x0,x1,y0,y1=x1,x0,y1,y0
        major=y1-y0; minor=abs(x1-x0); negative=x1<x0
    mismatch,slope,phase=choose_dda(major,minor)
    x,y=x0,y0; err=phase; points=[(x,y)]; errors=[err]
    for _ in range(major):
        total=err+slope; carry=total>=256; err=total&255
        if carry:
            if axis==0:y += -1 if negative else 1
            else:x += -1 if negative else 1
        if axis==0:x+=1
        else:y+=1
        points.append((x,y)); errors.append(err)
    if points[-1]!=(x1,y1): raise RuntimeError('DDA endpoint mismatch')
    return {'axis':axis,'negative':negative,'slope':slope,'phase':phase,'mismatch':mismatch,'points':points,'errors':errors}


def make_step_chunks(dda,start:int,end:int):
    pts=dda['points'][start:end+1]; count=len(pts); axis=dda['axis']
    startmod=(pts[0][0] if axis==0 else pts[0][1])&7
    decisions=[]
    for a,b in zip(pts,pts[1:]): decisions.append((a[1]!=b[1]) if axis==0 else (a[0]!=b[0]))
    decisions.append(False)
    chunks=[]; i=0; capacity=8-startmod
    while i<count:
        n=min(capacity,count-i); m=0
        for j in range(n):
            if decisions[i+j]:m|=0x80>>j
        chunks.append(m); i+=n; capacity=8
    return chunks


def encode_run(dda,start:int,end:int):
    x,y=dda['points'][start]; count=end-start+1
    if not 2<=count<=127: raise RuntimeError(f'run count {count}')
    offset=(y>>3)*320+(x>>3)*8
    ctl=(x&7)|((y&7)<<3)|(dda['axis']<<6)|(int(dda['negative'])<<7)
    return (offset&255,(offset>>8)&255,count,ctl,*make_step_chunks(dda,start,end))


def decode_record_points(rec):
    offlo,offhi,count,ctl=rec[:4]; masks=list(rec[4:])
    xmod=ctl&7; ymod=(ctl>>3)&7; axis=(ctl>>6)&1; neg=bool(ctl&0x80)
    off=offlo|(offhi<<8); cy,rem=divmod(off,320); cx=rem//8
    x=cx*8+xmod; y=cy*8+ymod
    mi=0; step=masks[mi]; mi+=1; pts=[(x,y)]; dominant=xmod if axis==0 else ymod
    for _ in range(count-1):
        carry=bool(step&0x80); step=(step<<1)&255
        if carry:
            if axis==0:y += -1 if neg else 1
            else:x += -1 if neg else 1
        if axis==0:x+=1
        else:y+=1
        dominant=(dominant+1)&7
        if dominant==0:
            if mi>=len(masks):raise RuntimeError('mask underrun')
            step=masks[mi]; mi+=1
        pts.append((x,y))
    if mi!=len(masks):raise RuntimeError('mask overrun')
    return pts


def _rotate_axis(p,a,axis='y'):
    x,y,z=p; c=math.cos(a); s=math.sin(a)
    if axis=='x': return x, y*c-z*s, y*s+z*c
    if axis=='y': return x*c+z*s, y, z*c-x*s
    if axis=='z': return x*c-y*s, x*s+y*c, z
    raise ValueError(f'unknown spin axis: {axis}')


def fit_scale(mesh:Mesh, frames:int, camera:Camera, margin:int=4, max_scale:float=1.4, spin_axis:str="y"):
    def ok(s):
        for fi in range(frames):
            a=2*math.pi*fi/frames
            for p in mesh.vertices:
                x,y,z0=_rotate_axis((p[0]*s,p[1]*s,p[2]*s),a,spin_axis); z=camera.distance+z0
                if z<=1: return False
                sx=camera.cx+camera.focal*x/z; sy=camera.cy-camera.focal*y/z
                if sx<margin or sx>W-1-margin or sy<margin or sy>H-1-margin:return False
        return True
    lo,hi=0.01,max_scale
    for _ in range(32):
        mid=(lo+hi)/2
        if ok(mid):lo=mid
        else:hi=mid
    return lo


def classify_feature_edges(mesh:Mesh, feature_angle:float=40.0):
    """Return edge->bool and counts for topology/crease feature edges.

    Boundary and non-manifold edges are always features. A normal manifold edge
    is a feature when the angle between its adjacent face normals is at least
    ``feature_angle`` degrees. This prevents low-poly structural creases from
    being discarded merely because both adjacent faces are back-facing.
    """
    ef=mesh.edge_faces(); fnorm=[face_normal(mesh,f) for f in mesh.faces]
    cos_limit=math.cos(math.radians(feature_angle))
    out={}; boundary=nonmanifold=crease=0
    for e in mesh.edges:
        adj=ef[e]
        if len(adj)==1:
            out[e]=True; boundary+=1
        elif len(adj)!=2:
            out[e]=True; nonmanifold+=1
        else:
            sharp=dot(fnorm[adj[0]],fnorm[adj[1]]) <= cos_limit
            out[e]=sharp
            if sharp: crease+=1
    return out, {'boundary':boundary,'nonmanifold':nonmanifold,'crease':crease,'features':sum(out.values()),'edges':len(out)}


def build_frames(mesh:Mesh, frames:int, camera:Camera, spin_axis:str="y", visibility_mode:str="surface", z_tolerance:float=Z_TOL, feature_angle:float=40.0) -> tuple[list[FrameBuild],int]:
    if not 1<=frames<=255: raise ValueError('frames must be 1..255')
    # Precompute face geometry in object space.
    fcent=[face_center(mesh,f) for f in mesh.faces]
    fnorm=[face_normal(mesh,f) for f in mesh.faces]
    tris=mesh.triangulated_faces()
    edges=mesh.edges; ef=mesh.edge_faces()
    feature_edges={}
    if visibility_mode == "surface_creases":
        feature_edges,_feature_stats=classify_feature_edges(mesh,feature_angle)
    all_frames=[]
    for fi in range(frames):
        angle=2*math.pi*fi/frames
        projected=[]
        for p0 in mesh.vertices:
            x,y,z0=_rotate_axis(p0,angle,spin_axis); z=camera.distance+z0
            sx=camera.cx+camera.focal*x/z; sy=camera.cy-camera.focal*y/z
            projected.append((sx,sy,1.0/z))
        front=[]
        for c0,n0 in zip(fcent,fnorm):
            px,py,pz0=_rotate_axis(c0,angle,spin_axis); nx,ny,nz=_rotate_axis(n0,angle,spin_axis); pz=camera.distance+pz0
            front.append((nx*px+ny*py+nz*pz)<0.0)
        zbuf=[0.0]*(W*H)
        zowner=[-1]*(W*H)
        if visibility_mode not in ("surface", "surface_features", "surface_creases", "frontface"):
            raise ValueError(f"unknown visibility mode: {visibility_mode}")
        # ``surface`` is winding-independent: rasterize every triangle and let
        # the reciprocal-depth buffer keep the nearest surface. This is much
        # more robust for imported open/non-manifold OBJ meshes, where face
        # winding may be imperfect or locally ambiguous. ``frontface`` retains
        # the historical Elite-style fast host-side cull for comparison.
        for facei,a,b,c in tris:
            if visibility_mode in ("surface", "surface_features", "surface_creases") or front[facei]:
                raster_triangle(zbuf,zowner,facei,projected[a],projected[b],projected[c])
        records=[]; touched=set(); raw=0; mism=[]
        for v0,v1 in edges:
            adjacent=ef[(v0,v1)]
            if visibility_mode == "frontface" and adjacent and not any(front[i] for i in adjacent):
                continue
            if (visibility_mode == "surface_features" and adjacent and len(adjacent)==2
                    and not any(front[i] for i in adjacent)):
                # Lightweight v0.3.1 semantics: closed-manifold edges whose
                # adjacent faces are both back-facing are culled before the
                # full surface Z-buffer test. Boundary/non-manifold edges are
                # retained. This keeps meshes such as sunflower_torus cheap.
                continue
            if (visibility_mode == "surface_creases" and adjacent and len(adjacent)==2
                    and not feature_edges[(v0,v1)] and not any(front[i] for i in adjacent)):
                # Crease-aware v0.3.2 semantics, retained as a separate mode:
                # sharp manifold creases survive back-face pre-culling and go
                # through the full surface Z-buffer visibility test.
                continue
            x0=int(round(projected[v0][0])); y0=int(round(projected[v0][1]))
            x1=int(round(projected[v1][0])); y1=int(round(projected[v1][1]))
            # Projected mesh is fitted; still guard a bad imported mesh.
            if not (0<=x0<W and 0<=x1<W and 0<=y0<H and 0<=y1<H):
                raise RuntimeError(f'frame {fi}: projected edge outside viewport: {(x0,y0)} {(x1,y1)}')
            dda=oriented_dda(x0,y0,x1,y1); mism.append(dda['mismatch']); pts=dda['points']
            q0=projected[v0][2]; q1=projected[v1][2]
            if pts[0]!=(x0,y0):q0,q1=q1,q0
            # Compare the edge against the surface buffer at the same screen-space
            # sample location. More importantly, an edge must never disappear merely
            # because one of *its own adjacent faces* won the Z-buffer pixel. That
            # self-occlusion showed up on open/non-manifold OBJ meshes (notably the
            # horse muzzle) as intermittent missing line segments while rotating.
            #
            # q=1/z is perspective-correct when interpolated linearly in screen space.
            # Project each raster pixel centre onto the original projected edge rather
            # than using DDA-step index, which also avoids depth drift on steep lines.
            sx0,sy0=projected[v0][0],projected[v0][1]
            sx1,sy1=projected[v1][0],projected[v1][1]
            ex=sx1-sx0; ey=sy1-sy0; el2=ex*ex+ey*ey
            adjacent_set=set(adjacent)
            vis=[]
            for x,y in pts:
                if el2>1e-12:
                    px=x+0.5; py=y+0.5
                    t=((px-sx0)*ex+(py-sy0)*ey)/el2
                    t=max(0.0,min(1.0,t))
                else:
                    t=0.0
                q=projected[v0][2]+(projected[v1][2]-projected[v0][2])*t
                pi=y*W+x
                own_surface=(zowner[pi] in adjacent_set)
                vis.append(own_surface or q>=zbuf[pi]-z_tolerance)
            start=None
            for k,v in enumerate(vis+[False]):
                if v and start is None:start=k
                elif not v and start is not None:
                    end=k-1
                    if end-start>=1:
                        # Runtime record count is 7-bit-ish by design (2..127
                        # plotted pixels). Generic OBJ/cube edges can be much
                        # longer than the torus edges, so split a long visible
                        # run into consecutive records instead of rejecting it.
                        seg_start=start
                        while seg_start<=end:
                            seg_end=min(end,seg_start+126)
                            if seg_end-seg_start<1:
                                # A one-pixel tail is already adjacent to the
                                # previous segment and can be safely omitted.
                                break
                            rec=encode_run(dda,seg_start,seg_end); exp=pts[seg_start:seg_end+1]
                            if decode_record_points(rec)!=exp:raise RuntimeError('encoded DDA verify failed')
                            records.append(rec); raw+=len(exp); touched.update(exp)
                            seg_start=seg_end+1
                    start=None
        if len(records)>255: raise RuntimeError(f'frame {fi}: {len(records)} visible runs >255')
        if not touched: raise RuntimeError(f'frame {fi}: no visible pixels')
        # clear touched character-cell runs, as in v0.8
        cells={(x>>3,y>>3) for x,y in touched}; spans=[]
        for cy in range(H//8):
            row=sorted(cx for cx,yy in cells if yy==cy)
            if not row:continue
            run0=prev=row[0]
            for cx in row[1:]+[None]:
                if cx is not None and cx==prev+1:prev=cx;continue
                off=cy*320+run0*8; count=prev-run0+1
                spans.append((off&255,(off>>8)&255,count))
                if cx is not None:run0=prev=cx
        all_frames.append(FrameBuild(records,spans,raw,len(touched),mism))
    return all_frames,len(edges)


def build_xchunk_tables():
    levels=[]; masks=[[0]*256 for _ in range(8)]
    for step in range(256):
        lev=0; rowm=[0]*8
        for i in range(8):
            rowm[lev]|=0x80>>i
            if step&(0x80>>i):lev+=1
        occ=0
        for i,m in enumerate(rowm):
            masks[i][step]=m
            if m:occ=i+1
        levels.append(occ)
    return levels,masks
