from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable
import math

Vec3 = tuple[float, float, float]

@dataclass
class Mesh:
    name: str
    vertices: list[Vec3]
    faces: list[tuple[int, ...]]
    # Optional wire-only edges. OBJ/procedural meshes normally derive their
    # edges from polygon faces. SVG artwork is fundamentally contour geometry,
    # so keeping explicit edges lets it become a real 3-D wire object without
    # inventing bogus filled faces or triangulating glyph holes.
    line_edges: list[tuple[int, int]] = field(default_factory=list)

    def copy(self, *, name: str | None = None) -> "Mesh":
        return Mesh(name or self.name, list(self.vertices), list(self.faces), list(self.line_edges))

    @property
    def edges(self) -> list[tuple[int, int]]:
        seen: set[tuple[int, int]] = set()
        out: list[tuple[int, int]] = []
        for face in self.faces:
            if len(face) < 2:
                continue
            for a, b in zip(face, face[1:] + face[:1]):
                e = (a, b) if a < b else (b, a)
                if e not in seen:
                    seen.add(e)
                    out.append(e)
        for a,b in self.line_edges:
            if a == b:
                continue
            e = (a,b) if a < b else (b,a)
            if e not in seen:
                seen.add(e)
                out.append(e)
        return out

    def edge_faces(self) -> dict[tuple[int, int], list[int]]:
        out: dict[tuple[int, int], list[int]] = {}
        for fi, face in enumerate(self.faces):
            for a, b in zip(face, face[1:] + face[:1]):
                e = (a, b) if a < b else (b, a)
                out.setdefault(e, []).append(fi)
        # Explicit wire edges deliberately have no owning surface. Hidden-line
        # modes therefore leave them alone unless real polygon geometry covers
        # them in the depth buffer.
        for a,b in self.line_edges:
            e=(a,b) if a < b else (b,a)
            out.setdefault(e,[])
        return out

    def triangulated_faces(self) -> list[tuple[int, int, int, int]]:
        """Return (face_index, a,b,c) fan triangles."""
        out = []
        for fi, face in enumerate(self.faces):
            if len(face) < 3:
                continue
            a = face[0]
            for i in range(1, len(face)-1):
                out.append((fi, a, face[i], face[i+1]))
        return out


def vadd(a: Vec3, b: Vec3) -> Vec3:
    return (a[0]+b[0], a[1]+b[1], a[2]+b[2])

def vsub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def vmul(a: Vec3, s: float) -> Vec3:
    return (a[0]*s, a[1]*s, a[2]*s)

def dot(a: Vec3, b: Vec3) -> float:
    return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]

def cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1]*b[2]-a[2]*b[1],
        a[2]*b[0]-a[0]*b[2],
        a[0]*b[1]-a[1]*b[0],
    )

def length(a: Vec3) -> float:
    return math.sqrt(dot(a,a))

def normalize(a: Vec3) -> Vec3:
    l = length(a)
    if l <= 1e-12:
        return (0.0,0.0,0.0)
    return (a[0]/l,a[1]/l,a[2]/l)


def face_center(mesh: Mesh, face: tuple[int, ...]) -> Vec3:
    n = float(len(face))
    return (
        sum(mesh.vertices[i][0] for i in face)/n,
        sum(mesh.vertices[i][1] for i in face)/n,
        sum(mesh.vertices[i][2] for i in face)/n,
    )


def face_normal(mesh: Mesh, face: tuple[int, ...]) -> Vec3:
    # Newell's method handles n-gons and is less fragile than first-triangle only.
    nx=ny=nz=0.0
    for ia, ib in zip(face, face[1:] + face[:1]):
        a = mesh.vertices[ia]; b = mesh.vertices[ib]
        nx += (a[1]-b[1])*(a[2]+b[2])
        ny += (a[2]-b[2])*(a[0]+b[0])
        nz += (a[0]-b[0])*(a[1]+b[1])
    return normalize((nx,ny,nz))


def mesh_center(mesh: Mesh) -> Vec3:
    if not mesh.vertices:
        return (0.0,0.0,0.0)
    xs=[p[0] for p in mesh.vertices]; ys=[p[1] for p in mesh.vertices]; zs=[p[2] for p in mesh.vertices]
    return ((min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2)


def _signed_component_volume(vertices: list[Vec3], faces: list[tuple[int, ...]], indices: list[int]) -> float:
    """Signed volume of a consistently wound polygon component.

    Faces are triangulated as fans. Positive volume means the conventional
    right-handed outward orientation. This works for concave closed meshes
    (including a torus); unlike a face-center-vs-object-center test, it does
    not assume that every surface normal points away from one global point.
    """
    vol6 = 0.0
    for fi in indices:
        face = faces[fi]
        if len(face) < 3:
            continue
        a = vertices[face[0]]
        for j in range(1, len(face) - 1):
            b = vertices[face[j]]
            c = vertices[face[j + 1]]
            vol6 += dot(a, cross(b, c))
    return vol6 / 6.0


def fix_winding_outward(mesh: Mesh) -> Mesh:
    """Make face winding consistent, then orient closed components outward.

    The old implementation flipped each face independently by comparing its
    normal with a vector from the mesh centre. That only works for convex or
    star-shaped meshes. A torus is concave: normals on the inside of the hole
    legitimately point *towards* the global centre, so that heuristic reversed
    the inner ring and broke hidden-line removal.

    This version first propagates winding across shared edges (adjacent faces
    must traverse a shared edge in opposite directions). For closed components
    it then uses signed volume to choose the global outward orientation. Open
    components keep their consistent orientation, with one whole-component
    centroid heuristic as a best-effort fallback; crucially, faces are never
    independently flipped based on concavity.
    """
    faces = [tuple(f) for f in mesh.faces if len(f) >= 3]
    if not faces:
        return Mesh(mesh.name, list(mesh.vertices), [], list(mesh.line_edges))

    # undirected edge -> [(face index, direction sign)]
    # sign +1 means low->high in that face, -1 means high->low.
    edge_uses: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for fi, face in enumerate(faces):
        for a, b in zip(face, face[1:] + face[:1]):
            if a == b:
                continue
            lo, hi = (a, b) if a < b else (b, a)
            sign = 1 if (a, b) == (lo, hi) else -1
            edge_uses.setdefault((lo, hi), []).append((fi, sign))

    # Build face adjacency constraints. If two faces traverse the shared edge
    # in the same direction, exactly one of them must be flipped.
    nbrs: list[list[tuple[int, bool]]] = [[] for _ in faces]
    for uses in edge_uses.values():
        if len(uses) < 2:
            continue
        # Manifold meshes have exactly two users. For non-manifold edges, tie
        # every other user to the first; this is still a useful best effort.
        base_fi, base_sign = uses[0]
        for other_fi, other_sign in uses[1:]:
            differ = (base_sign == other_sign)
            nbrs[base_fi].append((other_fi, differ))
            nbrs[other_fi].append((base_fi, differ))

    flip: list[bool | None] = [None] * len(faces)
    components: list[list[int]] = []
    for root in range(len(faces)):
        if flip[root] is not None:
            continue
        flip[root] = False
        comp=[]
        stack=[root]
        while stack:
            fi=stack.pop(); comp.append(fi)
            for fj, differ in nbrs[fi]:
                want = bool(flip[fi]) ^ differ
                if flip[fj] is None:
                    flip[fj] = want
                    stack.append(fj)
                elif bool(flip[fj]) != want:
                    # Non-orientable/non-manifold contradiction. Keep the first
                    # assignment rather than destroying an otherwise usable mesh.
                    pass
        components.append(comp)

    oriented=[]
    for fi, face in enumerate(faces):
        oriented.append(tuple(reversed(face)) if flip[fi] else face)

    # Decide outward orientation once per connected component, never per face.
    c0 = mesh_center(Mesh(mesh.name, list(mesh.vertices), oriented, list(mesh.line_edges)))
    for comp in components:
        comp_set=set(comp)
        closed=True
        for uses in edge_uses.values():
            users=[fi for fi,_ in uses if fi in comp_set]
            if users and len(users) != 2:
                closed=False
                break

        vol = _signed_component_volume(mesh.vertices, oriented, comp)
        flip_component = False
        if closed and abs(vol) > 1.0e-9:
            flip_component = vol < 0.0
        else:
            # Open meshes have no meaningful enclosed volume. Use one aggregate
            # vote for the whole component; unlike the old code this preserves
            # the relative orientation of concave neighbouring faces.
            score=0.0
            for fi in comp:
                f=oriented[fi]
                score += dot(face_normal(Mesh(mesh.name, mesh.vertices, oriented, list(mesh.line_edges)), f),
                             vsub(face_center(Mesh(mesh.name, mesh.vertices, oriented, list(mesh.line_edges)), f), c0))
            flip_component = score < 0.0

        if flip_component:
            for fi in comp:
                oriented[fi] = tuple(reversed(oriented[fi]))

    return Mesh(mesh.name, list(mesh.vertices), oriented, list(mesh.line_edges))


def normalize_mesh(mesh: Mesh, target_half_extent: float = 46.0) -> Mesh:
    if not mesh.vertices:
        raise ValueError("mesh has no vertices")
    xs=[p[0] for p in mesh.vertices]; ys=[p[1] for p in mesh.vertices]; zs=[p[2] for p in mesh.vertices]
    cx=(min(xs)+max(xs))/2; cy=(min(ys)+max(ys))/2; cz=(min(zs)+max(zs))/2
    hx=(max(xs)-min(xs))/2; hy=(max(ys)-min(ys))/2; hz=(max(zs)-min(zs))/2
    h=max(hx,hy,hz,1e-9)
    s=target_half_extent/h
    verts=[((x-cx)*s,(y-cy)*s,(z-cz)*s) for x,y,z in mesh.vertices]
    return Mesh(mesh.name, verts, list(mesh.faces), list(mesh.line_edges))


def rotate_xyz(p: Vec3, rx: float=0.0, ry: float=0.0, rz: float=0.0) -> Vec3:
    x,y,z=p
    if rx:
        c=math.cos(rx); s=math.sin(rx); y,z=y*c-z*s,y*s+z*c
    if ry:
        c=math.cos(ry); s=math.sin(ry); x,z=x*c+z*s,z*c-x*s
    if rz:
        c=math.cos(rz); s=math.sin(rz); x,y=x*c-y*s,x*s+y*c
    return x,y,z


def transform_mesh(mesh: Mesh, *, rx=0.0, ry=0.0, rz=0.0, scale=1.0) -> Mesh:
    return Mesh(mesh.name, [vmul(rotate_xyz(p,rx,ry,rz),scale) for p in mesh.vertices], list(mesh.faces), list(mesh.line_edges))


def mesh_diagnostics(mesh: Mesh) -> dict[str, int | dict[int,int]]:
    ef=mesh.edge_faces()
    boundary=sum(1 for users in ef.values() if len(users)==1)
    nonmanifold=sum(1 for users in ef.values() if len(users)>2)
    isolated=set(range(len(mesh.vertices)))
    for face in mesh.faces:
        isolated.difference_update(face)
    for a,b in mesh.line_edges:
        isolated.discard(a); isolated.discard(b)
    face_sizes: dict[int,int]={}
    for face in mesh.faces:
        face_sizes[len(face)]=face_sizes.get(len(face),0)+1
    return {
        'vertices': len(mesh.vertices),
        'edges': len(mesh.edges),
        'faces': len(mesh.faces),
        'boundary_edges': boundary,
        'nonmanifold_edges': nonmanifold,
        'isolated_vertices': len(isolated),
        'face_sizes': face_sizes,
    }
