from __future__ import annotations

"""Small dependency-free SVG -> C64 wire-mesh importer.

The C64 renderer wants vertices + edges, while SVG is mostly 2-D contour data.
This module flattens common SVG primitives and path commands to polylines,
simplifies them, flips SVG's Y-down coordinates to the toolkit's Y-up system,
and can give the contours a shallow Z extrusion.  The result is deliberately a
wire object: no fake front-face triangulation is required, so glyph holes and
concave logo outlines remain correct.
"""

from dataclasses import dataclass
import math
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from .mesh import Mesh
from .colors import (
    C64_PALETTE, c64_color_index, c64_color_name, nearest_c64_color,
    nearest_c64_color_index, parse_source_color,
)

Point2 = tuple[float, float]
Matrix = tuple[float, float, float, float, float, float]  # SVG a,b,c,d,e,f

_TOKEN_RE = re.compile(r"[AaCcHhLlMmQqSsTtVvZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
_TRANSFORM_RE = re.compile(r"([A-Za-z]+)\s*\(([^)]*)\)")
_NUM_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")

@dataclass
class SvgInfo:
    mesh: Mesh
    contours: int
    source_points: int
    simplified_points: int
    source_color: str | None
    c64_color: str
    source_colors: tuple[str, ...] = ()
    c64_colors: tuple[str, ...] = ()


# Backwards-compatible private alias for callers/tests from the v0.4 module.
_parse_css_color=parse_source_color


def _identity() -> Matrix:
    return (1.0,0.0,0.0,1.0,0.0,0.0)


def _mul(a: Matrix, b: Matrix) -> Matrix:
    # a(b(p))
    a1,b1,c1,d1,e1,f1=a; a2,b2,c2,d2,e2,f2=b
    return (
        a1*a2+c1*b2, b1*a2+d1*b2,
        a1*c2+c1*d2, b1*c2+d1*d2,
        a1*e2+c1*f2+e1, b1*e2+d1*f2+f1,
    )


def _apply(m: Matrix, p: Point2) -> Point2:
    a,b,c,d,e,f=m; x,y=p
    return (a*x+c*y+e,b*x+d*y+f)


def _parse_transform(value: str | None) -> Matrix:
    cur=_identity()
    if not value:return cur
    for name,args_s in _TRANSFORM_RE.findall(value):
        nums=[float(x) for x in _NUM_RE.findall(args_s)]
        name=name.lower()
        if name=='matrix' and len(nums)==6:
            t=tuple(nums)  # type: ignore[assignment]
        elif name=='translate' and nums:
            tx=nums[0]; ty=nums[1] if len(nums)>1 else 0.0
            t=(1,0,0,1,tx,ty)
        elif name=='scale' and nums:
            sx=nums[0]; sy=nums[1] if len(nums)>1 else sx
            t=(sx,0,0,sy,0,0)
        elif name=='rotate' and nums:
            a=math.radians(nums[0]); c=math.cos(a); s=math.sin(a)
            r=(c,s,-s,c,0,0)
            if len(nums)>=3:
                cx,cy=nums[1],nums[2]
                t=_mul((1,0,0,1,cx,cy),_mul(r,(1,0,0,1,-cx,-cy)))
            else:t=r
        elif name=='skewx' and nums:
            t=(1,0,math.tan(math.radians(nums[0])),1,0,0)
        elif name=='skewy' and nums:
            t=(1,math.tan(math.radians(nums[0])),0,1,0,0)
        else:
            continue
        # SVG transform lists apply in written order.
        cur=_mul(cur,t)
    return cur


def _style(elem: ET.Element) -> dict[str,str]:
    out={}
    raw=elem.get('style','')
    for item in raw.split(';'):
        if ':' in item:
            k,v=item.split(':',1); out[k.strip().lower()]=v.strip()
    for k in ('fill','stroke','stroke-width','display','visibility','opacity','fill-opacity','stroke-opacity'):
        if elem.get(k) is not None:out[k]=str(elem.get(k))
    return out


def _dist(a:Point2,b:Point2)->float:
    return math.hypot(a[0]-b[0],a[1]-b[1])


def _curve_steps(points:list[Point2], curve_step:float)->int:
    ln=sum(_dist(a,b) for a,b in zip(points,points[1:]))
    return max(2,min(64,int(math.ceil(ln/max(curve_step,0.25)))))


def _quad(p0:Point2,p1:Point2,p2:Point2,t:float)->Point2:
    u=1-t
    return (u*u*p0[0]+2*u*t*p1[0]+t*t*p2[0],u*u*p0[1]+2*u*t*p1[1]+t*t*p2[1])


def _cubic(p0:Point2,p1:Point2,p2:Point2,p3:Point2,t:float)->Point2:
    u=1-t
    return (u**3*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t**3*p3[0],
            u**3*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t**3*p3[1])


def _arc_points(p0:Point2, rx:float, ry:float, phi_deg:float, large:int, sweep:int, p1:Point2, curve_step:float)->list[Point2]:
    # SVG 1.1 endpoint-parameterized elliptical arc conversion.
    if rx==0 or ry==0 or _dist(p0,p1)<1e-12:return [p1]
    rx=abs(rx); ry=abs(ry); phi=math.radians(phi_deg%360.0); cp=math.cos(phi); sp=math.sin(phi)
    dx=(p0[0]-p1[0])/2; dy=(p0[1]-p1[1])/2
    xp=cp*dx+sp*dy; yp=-sp*dx+cp*dy
    lam=(xp*xp)/(rx*rx)+(yp*yp)/(ry*ry)
    if lam>1:
        k=math.sqrt(lam); rx*=k; ry*=k
    num=max(0.0,rx*rx*ry*ry-rx*rx*yp*yp-ry*ry*xp*xp)
    den=max(1e-30,rx*rx*yp*yp+ry*ry*xp*xp)
    coef=math.sqrt(num/den)
    if bool(large)==bool(sweep):coef=-coef
    cxp=coef*(rx*yp/ry); cyp=coef*(-ry*xp/rx)
    cx=cp*cxp-sp*cyp+(p0[0]+p1[0])/2
    cy=sp*cxp+cp*cyp+(p0[1]+p1[1])/2
    def vang(ux,uy,vx,vy):
        d=max(-1.0,min(1.0,ux*vx+uy*vy)); a=math.acos(d)
        if ux*vy-uy*vx<0:a=-a
        return a
    ux=(xp-cxp)/rx; uy=(yp-cyp)/ry
    vx=(-xp-cxp)/rx; vy=(-yp-cyp)/ry
    a0=vang(1,0,ux,uy); da=vang(ux,uy,vx,vy)
    if not sweep and da>0:da-=2*math.pi
    if sweep and da<0:da+=2*math.pi
    approx_len=max(rx,ry)*abs(da)
    n=max(2,min(96,int(math.ceil(approx_len/max(curve_step,0.25)))))
    out=[]
    for i in range(1,n+1):
        a=a0+da*i/n
        x=cx+cp*rx*math.cos(a)-sp*ry*math.sin(a)
        y=cy+sp*rx*math.cos(a)+cp*ry*math.sin(a)
        out.append((x,y))
    return out


def _flatten_path(d:str, curve_step:float)->list[tuple[list[Point2],bool]]:
    toks=_TOKEN_RE.findall(d.replace(',', ' '))
    i=0; cmd=None; cur=(0.0,0.0); start=(0.0,0.0); out=[]; pts=[]; closed=False
    last_cubic:Point2|None=None; last_quad:Point2|None=None
    arity={'M':2,'L':2,'H':1,'V':1,'C':6,'S':4,'Q':4,'T':2,'A':7,'Z':0}
    def flush():
        nonlocal pts,closed
        if len(pts)>=2:out.append((pts,closed))
        pts=[]; closed=False
    while i<len(toks):
        if toks[i].isalpha():
            cmd=toks[i]; i+=1
            if cmd.upper()=='Z':
                if pts and _dist(pts[-1],start)>1e-9:pts.append(start)
                cur=start; closed=True; flush(); last_cubic=last_quad=None; cmd=None; continue
        if cmd is None:raise ValueError('SVG path data begins without a command')
        up=cmd.upper(); rel=cmd.islower(); n=arity[up]
        if i+n>len(toks):raise ValueError(f'incomplete SVG path command {cmd}')
        if up=='M':
            x,y=map(float,toks[i:i+2]); i+=2
            if rel:x+=cur[0]; y+=cur[1]
            if pts:flush()
            cur=(x,y); start=cur; pts=[cur]; last_cubic=last_quad=None
            cmd='l' if rel else 'L'
            continue
        vals=list(map(float,toks[i:i+n])); i+=n
        old=cur
        if up=='L':
            x,y=vals; cur=((old[0]+x,old[1]+y) if rel else (x,y)); pts.append(cur)
        elif up=='H':
            x=vals[0]+old[0] if rel else vals[0]; cur=(x,old[1]); pts.append(cur)
        elif up=='V':
            y=vals[0]+old[1] if rel else vals[0]; cur=(old[0],y); pts.append(cur)
        elif up=='Q':
            x1,y1,x2,y2=vals
            if rel:x1+=old[0]; y1+=old[1]; x2+=old[0]; y2+=old[1]
            c=(x1,y1); end=(x2,y2); steps=_curve_steps([old,c,end],curve_step)
            pts.extend(_quad(old,c,end,j/steps) for j in range(1,steps+1)); cur=end; last_quad=c; last_cubic=None
        elif up=='T':
            x2,y2=vals
            if rel:x2+=old[0]; y2+=old[1]
            c=(2*old[0]-last_quad[0],2*old[1]-last_quad[1]) if last_quad is not None else old
            end=(x2,y2); steps=_curve_steps([old,c,end],curve_step)
            pts.extend(_quad(old,c,end,j/steps) for j in range(1,steps+1)); cur=end; last_quad=c; last_cubic=None
        elif up=='C':
            x1,y1,x2,y2,x3,y3=vals
            if rel:x1+=old[0]; y1+=old[1]; x2+=old[0]; y2+=old[1]; x3+=old[0]; y3+=old[1]
            c1=(x1,y1); c2=(x2,y2); end=(x3,y3); steps=_curve_steps([old,c1,c2,end],curve_step)
            pts.extend(_cubic(old,c1,c2,end,j/steps) for j in range(1,steps+1)); cur=end; last_cubic=c2; last_quad=None
        elif up=='S':
            x2,y2,x3,y3=vals
            if rel:x2+=old[0]; y2+=old[1]; x3+=old[0]; y3+=old[1]
            c1=(2*old[0]-last_cubic[0],2*old[1]-last_cubic[1]) if last_cubic is not None else old
            c2=(x2,y2); end=(x3,y3); steps=_curve_steps([old,c1,c2,end],curve_step)
            pts.extend(_cubic(old,c1,c2,end,j/steps) for j in range(1,steps+1)); cur=end; last_cubic=c2; last_quad=None
        elif up=='A':
            rx,ry,phi,large,sweep,x,y=vals
            if rel:x+=old[0]; y+=old[1]
            end=(x,y); pts.extend(_arc_points(old,rx,ry,phi,int(large),int(sweep),end,curve_step)); cur=end; last_cubic=last_quad=None
        if up not in ('C','S'):last_cubic=None
        if up not in ('Q','T'):last_quad=None
    if pts:flush()
    return out


def _rdp(points:list[Point2], eps:float)->list[Point2]:
    if len(points)<=2 or eps<=0:return points[:]
    a,b=points[0],points[-1]; dx=b[0]-a[0]; dy=b[1]-a[1]; den=dx*dx+dy*dy
    best=-1.0; idx=-1
    for i,p in enumerate(points[1:-1],1):
        if den<=1e-30:d=_dist(p,a)
        else:
            t=max(0.0,min(1.0,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den))
            q=(a[0]+t*dx,a[1]+t*dy); d=_dist(p,q)
        if d>best:best=d; idx=i
    if best>eps:
        l=_rdp(points[:idx+1],eps); r=_rdp(points[idx:],eps)
        return l[:-1]+r
    return [a,b]


def _simplify(points:list[Point2], closed:bool, eps:float)->list[Point2]:
    if not points:return []
    pts=[points[0]]
    for p in points[1:]:
        if _dist(p,pts[-1])>1e-8:pts.append(p)
    if closed and len(pts)>1 and _dist(pts[0],pts[-1])<1e-8:pts.pop()
    if len(pts)<=2:return pts
    if closed:
        # Split the ring at a point far from p0 so RDP does not see identical
        # endpoints and collapse the whole contour.
        k=max(range(1,len(pts)),key=lambda i:_dist(pts[0],pts[i]))
        a=_rdp(pts[:k+1],eps); b=_rdp(pts[k:]+[pts[0]],eps)
        simp=a[:-1]+b[:-1]
    else:simp=_rdp(pts,eps)
    return simp


def _points_attr(value:str)->list[Point2]:
    nums=[float(x) for x in _NUM_RE.findall(value)]
    return list(zip(nums[0::2],nums[1::2]))


def _shape_contours(elem:ET.Element, curve_step:float)->list[tuple[list[Point2],bool]]:
    tag=elem.tag.rsplit('}',1)[-1].lower()
    if tag=='path':return _flatten_path(elem.get('d',''),curve_step)
    if tag in ('polyline','polygon'):
        p=_points_attr(elem.get('points','')); return [(p,tag=='polygon')] if len(p)>=2 else []
    if tag=='line':
        p=[(float(elem.get('x1','0')),float(elem.get('y1','0'))),(float(elem.get('x2','0')),float(elem.get('y2','0')))]
        return [(p,False)]
    if tag=='rect':
        x=float(elem.get('x','0')); y=float(elem.get('y','0')); w=float(elem.get('width','0')); h=float(elem.get('height','0'))
        if w<=0 or h<=0:return []
        return [([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],True)]
    if tag in ('circle','ellipse'):
        cx=float(elem.get('cx','0')); cy=float(elem.get('cy','0'))
        rx=float(elem.get('r','0')) if tag=='circle' else float(elem.get('rx','0'))
        ry=rx if tag=='circle' else float(elem.get('ry','0'))
        if rx<=0 or ry<=0:return []
        n=max(12,min(96,int(math.ceil(2*math.pi*max(rx,ry)/max(curve_step,0.25)))))
        return [([(cx+rx*math.cos(2*math.pi*i/n),cy+ry*math.sin(2*math.pi*i/n)) for i in range(n)],True)]
    return []


def load_svg(path:Path, name:str|None=None, *, tolerance:float=3.0, curve_step:float=12.0,
             depth:float=5.0, connector_stride:int=4) -> SvgInfo:
    """Load SVG contours as a shallow 3-D wire object.

    ``depth`` is expressed in toolkit object units *after* normalisation to the
    usual ~92-unit full span. A depth of zero creates a flat 2-D wire plane.
    ``connector_stride`` controls how many front/back contour vertices are tied
    together; 1 gives a fully caged extrusion, larger values are cheaper.
    """
    path=Path(path)
    root=ET.parse(path).getroot()
    vb=[float(x) for x in _NUM_RE.findall(root.get('viewBox',''))]
    if len(vb)==4:vb_x,vb_y,vb_w,vb_h=vb
    else:
        def dim(v):
            m=_NUM_RE.search(v or ''); return float(m.group()) if m else 0.0
        vb_x=vb_y=0.0; vb_w=dim(root.get('width')); vb_h=dim(root.get('height'))

    raw_contours:list[tuple[list[Point2],bool,int|None,str|None]]=[]
    colors:list[tuple[int,tuple[int,int,int],str]]=[]  # c64 index,rgb,source

    def opacity_value(value:str)->float:
        value=value.strip()
        try:
            return max(0.0,min(1.0,float(value[:-1])/100.0 if value.endswith('%') else float(value)))
        except ValueError:
            return 1.0

    def opacity(st:dict[str,str],specific:str)->float:
        return opacity_value(st.get('opacity','1'))*opacity_value(st.get(specific,'1'))

    def shape_color(st:dict[str,str])->tuple[int|None,tuple[int,int,int]|None,str|None]:
        # A wire contour represents the SVG stroke when one exists; otherwise
        # its fill supplies the contour colour. This also handles the common
        # black-fill/yellow-stroke logo export without treating black as canvas.
        for kind in ('stroke','fill'):
            if opacity(st,f'{kind}-opacity')<=0:
                continue
            if kind=='stroke':
                try:
                    if float(st.get('stroke-width','1'))<=0:
                        continue
                except ValueError:
                    pass
            source=st.get(kind)
            rgb=parse_source_color(source)
            if rgb is not None:
                return nearest_c64_color_index(rgb),rgb,str(source)
        return None,None,None

    def walk(elem:ET.Element,parent_m:Matrix,parent_style:dict[str,str]):
        st=dict(parent_style); st.update(_style(elem))
        if st.get('display')=='none' or st.get('visibility')=='hidden':return
        m=_mul(parent_m,_parse_transform(elem.get('transform')))
        tag=elem.tag.rsplit('}',1)[-1].lower()
        shapes=_shape_contours(elem,curve_step)
        # Ignore a full-canvas rectangle: in exported logos it is almost always
        # the artwork background, not part of the vector object itself.
        if tag=='rect' and shapes and vb_w>0 and vb_h>0:
            pts,_=shapes[0]; xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
            full=(abs(min(xs)-vb_x)<1e-6 and abs(min(ys)-vb_y)<1e-6 and abs(max(xs)-(vb_x+vb_w))<1e-6 and abs(max(ys)-(vb_y+vb_h))<1e-6)
            if full:shapes=[]
        if shapes:
            color_index,rgb,source=shape_color(st)
            for pts,closed in shapes:
                raw_contours.append(([_apply(m,p) for p in pts],closed,color_index,source))
            if color_index is not None and rgb is not None and source is not None:
                colors.append((color_index,rgb,source))
        for child in list(elem):walk(child,m,st)
    walk(root,_identity(),{})
    if not raw_contours:raise ValueError(f'{path}: no supported visible SVG vector contours found')

    contours=[]; source_points=0
    for pts,closed,color_index,source in raw_contours:
        source_points+=len(pts)
        simp=_simplify(pts,closed,max(0.0,tolerance))
        if len(simp)>=2:contours.append((simp,closed,color_index,source))
    if not contours:raise ValueError(f'{path}: SVG contours vanished after simplification')

    # Convert SVG Y-down -> toolkit Y-up. Centreing/scaling is handled by the
    # normal mesh pipeline, but source span is needed to express Z extrusion in
    # normalised toolkit units.
    flat=[p for pts,_closed,_color,_source in contours for p in pts]
    xs=[p[0] for p in flat]; ys=[p[1] for p in flat]
    span=max(max(xs)-min(xs),max(ys)-min(ys),1e-9)
    source_depth=max(0.0,depth)*span/92.0
    zf=-source_depth/2; zb=source_depth/2
    verts=[]; edges=[]; edge_colors=[]
    stride=max(1,int(connector_stride))
    for pts,closed,color_index,_source in contours:
        front=[]
        for x,y in pts:
            front.append(len(verts)); verts.append((x,-y,zf))
        count=len(front); lim=count if closed else count-1
        for j in range(lim):
            edges.append((front[j],front[(j+1)%count])); edge_colors.append(color_index)
        if source_depth>0:
            back=[]
            for x,y in pts:
                back.append(len(verts)); verts.append((x,-y,zb))
            for j in range(lim):
                edges.append((back[j],back[(j+1)%count])); edge_colors.append(color_index)
            for j in range(0,count,stride):
                edges.append((front[j],back[j])); edge_colors.append(color_index)
            if not closed and count>1 and (count-1)%stride:
                edges.append((front[-1],back[-1])); edge_colors.append(color_index)

    chosen=next((item for item in colors if item[0]!=0),colors[0] if colors else None)
    source_color=chosen[2] if chosen else None
    c64=c64_color_name(chosen[0]) if chosen else 'white'
    source_colors=tuple(dict.fromkeys(source for _index,_rgb,source in colors))
    c64_colors=tuple(dict.fromkeys(c64_color_name(index) for index,_rgb,_source in colors))
    mesh=Mesh(name or path.stem.upper(),verts,[],edges,[],edge_colors)
    return SvgInfo(
        mesh,len(contours),source_points,
        sum(len(points) for points,_closed,_color,_source in contours),
        source_color,c64,source_colors,c64_colors,
    )
