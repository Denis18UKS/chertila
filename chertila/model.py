from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Sequence


class LineStyle(str, Enum):
    SOLID = "solid"
    CENTER = "center"
    DIMENSION = "dimension"
    CONSTRUCTION = "construction"


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Line:
    start: Point
    end: Point
    style: LineStyle = LineStyle.SOLID


@dataclass(frozen=True)
class Circle:
    center: Point
    radius: float
    style: LineStyle = LineStyle.SOLID


@dataclass(frozen=True)
class Arc:
    center: Point
    radius: float
    start_angle: float
    end_angle: float
    style: LineStyle = LineStyle.SOLID


@dataclass(frozen=True)
class Polyline:
    points: Sequence[Point]
    closed: bool = False
    style: LineStyle = LineStyle.SOLID


@dataclass(frozen=True)
class Text:
    position: Point
    value: str
    size: float = 5.0
    style: LineStyle = LineStyle.DIMENSION


@dataclass(frozen=True)
class Drawing:
    name: str
    width: float
    height: float
    orientation: str
    entities: tuple[Line | Circle | Arc | Polyline | Text, ...] = field(default_factory=tuple)

    def bounds(self) -> tuple[float, float, float, float]:
        xs: list[float] = []
        ys: list[float] = []
        for entity in self.entities:
            if isinstance(entity, Line):
                xs.extend([entity.start.x, entity.end.x])
                ys.extend([entity.start.y, entity.end.y])
            elif isinstance(entity, Circle | Arc):
                xs.extend([entity.center.x - entity.radius, entity.center.x + entity.radius])
                ys.extend([entity.center.y - entity.radius, entity.center.y + entity.radius])
            elif isinstance(entity, Polyline):
                xs.extend(point.x for point in entity.points)
                ys.extend(point.y for point in entity.points)
            elif isinstance(entity, Text):
                xs.append(entity.position.x)
                ys.append(entity.position.y)
        if not xs or not ys:
            return (0, 0, self.width, self.height)
        return (min(xs), min(ys), max(xs), max(ys))

    def with_entities(self, entities: Iterable[Line | Circle | Arc | Polyline | Text]) -> "Drawing":
        return Drawing(self.name, self.width, self.height, self.orientation, tuple(entities))
