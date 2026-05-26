from __future__ import annotations

from typing import Iterable, Tuple


Point2D = Tuple[float, float]


def point_in_polygon(point: Point2D, polygon: Iterable[Point2D]) -> bool:
    x, y = point
    vertices = list(polygon)
    inside = False
    j = len(vertices) - 1
    for i in range(len(vertices)):
        xi, yi = vertices[i]
        xj, yj = vertices[j]
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) + 1e-9) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def line_side(point: Point2D, start: Point2D, end: Point2D) -> float:
    return (end[0] - start[0]) * (point[1] - start[1]) - (end[1] - start[1]) * (point[0] - start[0])
