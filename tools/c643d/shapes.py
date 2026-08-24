from __future__ import annotations
import math
from .mesh import Mesh


def torus(major_segments: int=10, minor_segments: int=5, major_radius: float=34.0, minor_radius: float=14.0) -> Mesh:
    if major_segments < 3 or minor_segments < 3:
        raise ValueError("torus segment counts must be >= 3")
    v=[]
    for iu in range(major_segments):
        u=2*math.pi*iu/major_segments
        cu,su=math.cos(u),math.sin(u)
        for iv in range(minor_segments):
            t=2*math.pi*iv/minor_segments
            a=major_radius+minor_radius*math.cos(t)
            v.append((a*cu, minor_radius*math.sin(t), a*su))
    f=[]
    for iu in range(major_segments):
        for iv in range(minor_segments):
            a=iu*minor_segments+iv
            b=((iu+1)%major_segments)*minor_segments+iv
            c=((iu+1)%major_segments)*minor_segments+((iv+1)%minor_segments)
            d=iu*minor_segments+((iv+1)%minor_segments)
            f.append((a,b,c,d))
    return Mesh("TORUS",v,f)


def cube() -> Mesh:
    v=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
    f=[(0,3,2,1),(4,5,6,7),(0,4,7,3),(1,2,6,5),(0,1,5,4),(3,7,6,2)]
    return Mesh("CUBE",v,f)


def sphere(lat_segments: int=6, lon_segments: int=10) -> Mesh:
    if lat_segments < 3 or lon_segments < 3:
        raise ValueError("sphere segments must be >=3")
    v=[(0.0,1.0,0.0)]
    for ilat in range(1,lat_segments):
        phi=math.pi*ilat/lat_segments
        y=math.cos(phi); r=math.sin(phi)
        for ilon in range(lon_segments):
            t=2*math.pi*ilon/lon_segments
            v.append((r*math.cos(t),y,r*math.sin(t)))
    south=len(v); v.append((0.0,-1.0,0.0))
    f=[]
    # top
    for j in range(lon_segments):
        f.append((0,1+j,1+(j+1)%lon_segments))
    # middle quads
    for i in range(lat_segments-2):
        a0=1+i*lon_segments; b0=a0+lon_segments
        for j in range(lon_segments):
            f.append((a0+j,b0+j,b0+(j+1)%lon_segments,a0+(j+1)%lon_segments))
    # bottom
    base=1+(lat_segments-2)*lon_segments
    for j in range(lon_segments):
        f.append((south,base+(j+1)%lon_segments,base+j))
    return Mesh("SPHERE",v,f)


def choose_torus_segments(polycount: int) -> tuple[int,int]:
    if polycount < 9:
        raise ValueError("torus polycount must be >= 9")
    # Target roughly 2:1 major:minor segmentation, choose product close to request.
    nv=max(3,round(math.sqrt(polycount/2)))
    nu=max(3,round(polycount/nv))
    return nu,nv


def choose_sphere_segments(polycount: int) -> tuple[int,int]:
    if polycount < 12:
        raise ValueError("sphere polycount must be >= 12")
    lat=max(3,round(math.sqrt(polycount/2)))
    lon=max(3,round(polycount/lat))
    return lat,lon


def choose_torus_segments_by_vertices(vertices: int) -> tuple[int,int]:
    # A procedural torus has exactly major*minor vertices and faces.
    return choose_torus_segments(vertices)


def choose_sphere_segments_by_vertices(vertices: int) -> tuple[int,int]:
    if vertices < 8:
        raise ValueError("sphere vertex target must be >= 8")
    # sphere() emits 2 + (lat-1)*lon vertices. Search nearby practical grids.
    best=None
    for lat in range(3,65):
        for lon in range(3,129):
            actual=2+(lat-1)*lon
            score=(abs(actual-vertices), abs(lon-2*lat), actual)
            if best is None or score<best[0]:
                best=(score,lat,lon)
    return best[1],best[2]
