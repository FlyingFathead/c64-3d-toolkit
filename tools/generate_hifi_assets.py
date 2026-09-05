#!/usr/bin/env python3
"""Generate the separate title-art-inspired HiFi meshes.

Only regeneration needs numpy/scipy; importing/building the committed OBJ files
uses the toolkit's normal dependency-free path. Coordinates: Y up, +X muzzle.
"""
from pathlib import Path
import math, json, sys
import numpy as np
from scipy.spatial import Delaunay
sys.path.insert(0,str(Path(__file__).resolve().parent))
from c643d.mesh import Mesh, fix_winding_outward, mesh_diagnostics
from c643d.colors import C64_PALETTE
ROOT=Path(__file__).resolve().parents[1]

class Model:
    def __init__(self,name): self.name=name;self.v=[];self.f=[];self.m=[];self.groups=[];self.group='body'
    def vertex(self,p): self.v.append(tuple(float(x) for x in p));return len(self.v)-1
    def face(self,ids,mat): self.f.append(tuple(ids));self.m.append(mat);self.groups.append(self.group)
    def loop(self,pts): return [self.vertex(p) for p in pts]
    def bridge(self,a,b,mat,tri=False):
        for i in range(len(a)):
            j=(i+1)%len(a)
            if tri:
                self.face((a[i],a[j],b[j]),mat);self.face((a[i],b[j],b[i]),mat)
            else:self.face((a[i],a[j],b[j],b[i]),mat)
    def save(self,rotate):
        mesh=fix_winding_outward(Mesh(self.name,self.v,self.f))
        p=ROOT/'objects'/self.name
        lines=['# Original title-art-inspired faceted mesh; Y up, authored by Harry + Astra.',
               '# Independent closed components may intersect at their attachment points.',
               f'mtllib {self.name}.mtl',f'o {self.name}','s off']
        lines += ['v '+' '.join(f'{x:.7f}' for x in v) for v in self.v]
        old=None
        for f,m,g in zip(mesh.faces,self.m,self.groups):
            if old!=(m,g):lines.extend([f'g {g}',f'usemtl {m}']);old=(m,g)
            lines.append('f '+' '.join(str(i+1) for i in f))
        p.with_suffix('.obj').write_text('\n'.join(lines)+'\n')
        materials=[]
        for m in sorted(set(self.m)):
            rgb=C64_PALETTE[m][1]
            materials += [f'newmtl {m}','Ka 0.03 0.02 0.04','Kd '+' '.join(f'{c/255:.6f}' for c in rgb),'Ks 0.16 0.16 0.2','Ns 28','d 1','illum 2','']
        p.with_suffix('.mtl').write_text('# Kd maps exactly to native C64 colours. Ks/Ns serve desktop viewers only.\n'+'\n'.join(materials))
        p.with_suffix('.json').write_text(json.dumps(dict(name=self.name.replace('_',' ').upper(),file=p.name+'.obj',materials=[p.name+'.mtl'],use_colors=True,up_axis='y',spin_axis='y',rotate=rotate,scale=1,visibility='surface_features',z_tolerance=0.00008 if self.name=='horse_head_hifi' else 0.00035,notes='Separate HiFi title-art interpretation. Static facet materials, not runtime lighting. Original assets unchanged.'),indent=2)+'\n')
        diagnostics=mesh_diagnostics(mesh)
        assert diagnostics['boundary_edges']==0 and diagnostics['nonmanifold_edges']==0,diagnostics
        print(self.name,diagnostics)

def inside(p,poly):
    x,y=p;out=False
    for (a,b),(c,d) in zip(poly,poly[1:]+poly[:1]):
        if (b>y)!=(d>y) and x<(c-a)*(y-b)/(d-b)+a:out=not out
    return out

def horse():
    m=Model('horse_head_hifi')
    # Profile follows the arched nape, high poll, sloping forehead, long muzzle,
    # rounded lips, hanging jaw, and concave throat into a broad bust base.
    border=[(-1.12,-2.05),(-1.13,-1.05),(-1.08,.05),(-.94,1.02),(-.70,1.72),(-.34,2.17),(.04,2.25),(.40,1.98),(.70,1.52),(1.05,1.02),(1.48,.54),(1.79,.23),(1.84,-.16),(1.64,-.40),(1.28,-.37),(.87,-.15),(.42,.07),(.14,.32),(.02,-.47),(.26,-1.24),(.56,-2.05)]
    interior=[(-.62,-1.65),(-.28,-1.13),(-.66,-.55),(-.53,.35),(-.38,1.10),(-.13,1.68),(.24,1.37),(.27,.77),(.59,.57),(.83,.35),(1.18,.30),(1.50,.05),(-.10,-.04)]
    pts=border+interior;n=len(pts);nb=len(border)
    # Thin along silhouette, fuller through cheek and lower neck.
    bw=[.44,.43,.40,.34,.27,.24,.25,.27,.26,.235,.245,.29,.28,.24,.235,.28,.36,.32,.35,.42,.47]
    iw=[.66,.60,.57,.55,.48,.41,.49,.60,.48,.405,.365,.355,.48]
    widths=bw+iw
    sides=[]
    for sign in (-1,1):sides.append(m.loop([(x,y,sign*w) for (x,y),w in zip(pts,widths)]))
    def colour(x,y,z=0):
        if x>1.45:return 'cyan'
        if x>.80 and y>-.5:return 'light_blue'
        if y<-.5 and z>.1:return 'blue'
        return 'purple'
    tris=[]
    for f in Delaunay(np.array(pts)).simplices:
        vv=[pts[i] for i in f]
        if not inside(tuple(np.mean(vv,axis=0)),border):continue
        # Exclude triangles bridging the concave throat.
        tris.append(tuple(int(i) for i in f))
    # Constrain the concave throat edge: Delaunay omits this narrow wedge.
    if frozenset((17,18,33)) not in {frozenset(t) for t in tris}:
        tris.append((17,18,33))
    for side in sides:
        for f in tris:
            c=np.mean([m.v[side[i]] for i in f],axis=0)
            m.face([side[i] for i in f],colour(*c))
    # A centre seam gives nose bridge, nape, underside and flat base real depth.
    mid=m.loop([(x,y,0) for x,y in border])
    for i in range(nb):
        j=(i+1)%nb
        for side in sides:
            c=np.mean([m.v[side[i]],m.v[side[j]]],axis=0)
            m.face((side[i],side[j],mid[j],mid[i]),colour(*c))
    # Two sculpted ears, with an inset front cup and swept tips.
    for sign in (-1,1):
        m.group='ear_left' if sign<0 else 'ear_right'
        z=sign*.38
        base=m.loop([(-.36,2.05,z-.115),(.06,2.13,z-.10),(.05,2.18,z+.10),(-.35,2.10,z+.115)])
        rim=m.loop([(-.32,2.56,z-.11),(-.05,2.57,z-.07),(-.04,2.59,z+.06),(-.31,2.57,z+.11)])
        tip=m.vertex((-.12,3.03,z+sign*.10))
        m.face(base,'purple');m.bridge(base,rim,'purple')
        for i in range(4):m.face((rim[i],rim[(i+1)%4],tip),'light_blue' if i==1 else 'purple')
        # The existing ear side carries the inner-ear colour without duplicate faces.
        m.m[-3]='blue'
    # Raised almond brow/eye and nostril rings; closed shallow reliefs.
    for sign in (-1,1):
        for name,cx,cy,cz,rx,ry,mat in [('eye',.26,1.36,.590,.155,.105,'light_blue'),('nostril',1.48,.08,.450,.15,.16,'cyan')]:
            m.group=f'{name}_{sign}'
            ring=m.loop([(cx+rx*math.cos(t),cy+ry*math.sin(t),sign*(cz+.018)) for t in [2*math.pi*i/6 for i in range(6)]])
            back=m.vertex((cx,cy,sign*(cz-.17)))
            m.face(ring,mat)
            for i in range(6):
                j=(i+1)%6;m.face((ring[j],ring[i],back),'blue' if name=='eye' else 'light_blue')
    m.v=[(x*1.20,y,z) for x,y,z in m.v]
    m.save([0,25,-3])

def sunflower():
    m=Model('sunflower_torus_hifi');m.group='torus'
    major=20;minor=5;cy=.78
    rings=[]
    for i in range(major):
        a=2*math.pi*i/major
        rings.append(m.loop([((.79+.145*math.cos(b))*math.cos(a),cy+(.79+.145*math.cos(b))*math.sin(a),.145*math.sin(b)) for b in [2*math.pi*j/minor for j in range(minor)]]))
    # Flower faces -Z: brown seed-ring front/inner rim, green +Z backing.
    for i in range(major):
        for j in range(minor):m.face((rings[i][j],rings[(i+1)%major][j],rings[(i+1)%major][(j+1)%minor],rings[i][(j+1)%minor]),'brown' if j in (2,3,4) else 'green')
    # Unequal twisted petal tips add life while preserving radial readability.
    for i in range(16):
        m.group=f'petal_{i:02d}';a=2*math.pi*i/16;length=.49+.055*math.sin(i*2.39996);twist=.035*math.sin(i*1.8)
        def pt(r,t,z):return (r*math.cos(a)-t*math.sin(a),cy+r*math.sin(a)+t*math.cos(a),z)
        outline=m.loop([pt(.90,-.052,.0),pt(1.10,-.145,.01),pt(.94+length,twist,-.13-.05*math.cos(i*1.7)),pt(1.13,.145,.035),pt(.90,.055,0)])
        front=m.vertex(pt(1.13,0,-.15))
        m.face(outline,'yellow')
        for j in range(5):
            k=(j+1)%5;m.face((outline[j],outline[k],front),'yellow')
    # Curved tapered stem, elliptical section.
    m.group='stem';stem=[]
    for x,y,r in [(-.14,-2.10,.060),(-.12,-1.55,.063),(-.04,-.98,.058),(.015,-.35,.050),(0,.04,.040)]:
        stem.append(m.loop([(x+r*math.cos(t),y,.10+r*math.sin(t)) for t in [2*math.pi*j/5 for j in range(5)]]))
    m.face(stem[0],'green')
    for a,b in zip(stem,stem[1:]):m.bridge(a,b,'green')
    m.face(stem[-1],'green')
    for sign in (-1,1):
        m.group=f'leaf_{sign}';y0=-1.45 if sign<0 else -1.15
        # Leaf perimeter + raised midrib at three stations, closed underside.
        stations=[(-.10,y0,.11,.035),(.32*sign-.10,y0+.30,.04,.21),(.68*sign-.10,y0+.44,-.04,.18),(.92*sign-.10,y0+.51,-.11,0)]
        left=[];right=[];ridge=[]
        for x,y,z,w in stations:
            left.append(m.vertex((x,y-w,z+.035)));right.append(m.vertex((x,y+w,z+.035)));ridge.append(m.vertex((x,y,z-.075)))
        for j in range(3):
            for edge in (left,right):m.face((ridge[j],edge[j],edge[j+1],ridge[j+1]),'light_green' if sign>0 and edge==right else 'green')
            m.face((left[j],right[j],right[j+1],left[j+1]),'green')
        m.face((left[0],ridge[0],right[0]),'green')
    # Weld coincident leaf tips; drop degenerate faces introduced by welding.
    unique=[];lookup={};remap={}
    for i,v in enumerate(m.v):
        key=tuple(round(x,7) for x in v)
        if key not in lookup:lookup[key]=len(unique);unique.append(v)
        remap[i]=lookup[key]
    ff=[];mm=[];gg=[]
    for f,mat,g in zip(m.f,m.m,m.groups):
        ids=list(dict.fromkeys(remap[i] for i in f))
        if len(ids)>=3:ff.append(tuple(ids));mm.append(mat);gg.append(g)
    m.v=unique;m.f=ff;m.m=mm;m.groups=gg
    m.save([0,-14,7])

if __name__=='__main__':horse();sunflower()
