"""Host-side camera clipping; no generated vertices alter source topology."""
from __future__ import annotations

NEAR_PLANE = 1.0e-6


def clip_line_near(a, b, near=NEAR_PLANE):
    """Clip a camera-space segment to z >= near, preserving endpoint order."""
    if a[2] < near and b[2] < near:
        return None
    if a[2] >= near and b[2] >= near:
        return a, b
    t = (near - a[2]) / (b[2] - a[2])
    hit = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), near)
    return (hit, b) if a[2] < near else (a, hit)


def clip_polygon(points, signed_distance):
    """Sutherland-Hodgman clipping, interpolating every vertex attribute."""
    if not points:
        return []
    result = []
    previous = points[-1]
    dp = signed_distance(previous)
    for current in points:
        dc = signed_distance(current)
        if (dp >= 0) != (dc >= 0):
            t = dp / (dp - dc)
            result.append(tuple(a + t * (b - a) for a, b in zip(previous, current)))
        if dc >= 0:
            result.append(current)
        previous, dp = current, dc
    return result


def project_clipped_triangle(points, project, *, width, height, near=NEAR_PLANE):
    """Clip in camera space, then clip screen x/y and reciprocal depth together."""
    polygon = clip_polygon(points, lambda p: p[2] - near)
    projected = [project((p[0], p[1], max(near, p[2]))) for p in polygon]
    # Raster sample centres are x+.5/y+.5, so keep the full raster rectangle.
    for distance in (lambda p: p[0], lambda p: width - p[0],
                     lambda p: p[1], lambda p: height - p[1]):
        projected = clip_polygon(projected, distance)
    return [(projected[0], projected[i], projected[i+1])
            for i in range(1, len(projected)-1)]
