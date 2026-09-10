#!/usr/bin/env python3
"""Deterministic, Blender-free Demo Cart 2.0 preview material. No demo imports."""
from pathlib import Path
import json
import math

HERE = Path(__file__).resolve().parent
TAU = 2 * math.pi
PALETTE = [3, 14, 6, 4, 10, 7, 1]


def rotate(v, a, b, c=0):
    x, y, z = v
    y, z = y*math.cos(a)-z*math.sin(a), y*math.sin(a)+z*math.cos(a)
    x, z = x*math.cos(b)+z*math.sin(b), -x*math.sin(b)+z*math.cos(b)
    return (x*math.cos(c)-y*math.sin(c), x*math.sin(c)+y*math.cos(c), z)


def save(slug, title, topology, samples, motion, focal=170):
    frames = []
    for i in range(samples):
        points = motion(TAU*i/samples)
        frames.append(dict(source_frame=i, vertices=[[round(x, 7) for x in p] for p in points],
                           projection=dict(fx=focal, fy=focal, cx=160, cy=96)))
    data = dict(format='c643dscene', version=1, name=title, topology=topology,
                source=dict(fps=25, sample_step=1), frames=frames)
    (HERE/'scenes'/f'{slug}.c643dscene').write_text(json.dumps(data, separators=(',', ':'))+'\n')


def main():
    (HERE/'scenes').mkdir(exist_ok=True)
    # A twisting perspective tunnel: coloured rings and longitudinal rails.
    rings, sides = 7, 8
    edges = [(r*sides+j, r*sides+(j+1)%sides) for r in range(rings) for j in range(sides)]
    edges += [(r*sides+j, (r+1)*sides+j) for r in range(rings-1) for j in range(0,sides,2)]
    def tunnel(t):
        out = []
        for r in range(rings):
            z = 2.4+r*.85
            for j in range(sides):
                a=TAU*j/sides + .26*r + .38*math.sin(t+r*.5)
                out.append((1.15*math.cos(a)+.24*math.sin(t+r*.4),
                            1.15*math.sin(a)+.18*math.cos(2*t+r*.4),z))
        return out
    save('twist-tunnel','TWIST TUNNEL',dict(faces=[],line_edges=edges,
         line_colors=[PALETTE[(i//sides)%7] for i in range(len(edges))]),48,tunnel)
    # A continuously deforming ribbon with real hidden-surface edge removal.
    count=24
    faces=[(2*j,2*j+1,2*j+3,2*j+2) for j in range(count-1)]
    def ribbon(t):
        out=[]
        for j in range(count):
            u=-2.4+4.8*j/(count-1)
            twist=1.3*u+t
            for side in (-1,1):
                p=(u,.50*side*math.cos(twist)+.24*math.sin(u*2+t),.50*side*math.sin(twist))
                x,y,z=rotate(p,.4*math.sin(t),.35*math.sin(t),.23*math.cos(t))
                out.append((x,y,z+6))
        return out
    save('ribbon-dance','RIBBON DANCE',dict(faces=faces,face_colors=[PALETTE[j%7] for j in range(count-1)]),48,ribbon)
    # Three independently tumbling cubes pass in front of and behind each other.
    cube=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
    cube_faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(1,2,6,5),(0,4,7,3)]
    faces=[tuple(k+8*j for k in f) for j in range(3) for f in cube_faces]
    def cubes(t):
        out=[]
        for j in range(3):
            phase=t+j*TAU/3
            for v in cube:
                x,y,z=rotate(tuple(.53*k for k in v), t*(j+1), -t+j, t)
                out.append((x+1.35*math.cos(phase),y+.7*math.sin(phase*2),z+6+1.3*math.sin(phase)))
        return out
    save('orbital-cubes','ORBITAL CUBES',dict(faces=faces,face_colors=[PALETTE[(j//6*2+j%3)%7] for j in range(18)]),48,cubes)
    # Perspective wave lattice: interference, depth and camera rocking.
    nx,nz=11,8
    edges=[(z*nx+x,z*nx+x+1) for z in range(nz) for x in range(nx-1)]
    edges += [(z*nx+x,(z+1)*nx+x) for z in range(nz-1) for x in range(nx)]
    def waves(t):
        out=[]
        for j in range(nz):
            z=j*.5
            for i in range(nx):
                x=(i-5)*.42
                y=.25*math.sin(x*2+t)+.20*math.sin(z*2-2*t)-.6
                px,py,pz=rotate((x,y,z-1.75),.42+.1*math.sin(t),.18*math.sin(t))
                out.append((px,py,pz+5.8))
        return out
    save('wave-lattice','WAVE LATTICE',dict(faces=[],line_edges=edges,
         line_colors=[PALETTE[(i//nx)%7] for i in range(len(edges))]),48,waves)
    print('Generated four independent 48-sample scenes in', HERE/'scenes')


if __name__ == '__main__':
    main()
