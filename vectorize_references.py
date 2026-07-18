#!/usr/bin/env python3
"""Vectoriza las referencias raster de BUCLE como paths SVG editables.

Solo usa Python estándar e ImageMagick. Clasifica las tintas roja y blanca,
extrae sus contornos y los simplifica sin insertar la imagen raster en el SVG.
"""
from __future__ import annotations

import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "references-svg"
SOURCES = [
    "BOCAS.png",
    "DIENTE.png",
    "DIENTES.png",
    "JUNTOS.png",
    "LIP.png",
    "boca y dientes.png",
]
MAX_SIDE = 1800
EPSILON = 1.35
MIN_AREA = 10.0


def image_size(path: Path) -> tuple[int, int]:
    value = subprocess.check_output(
        ["identify", "-format", "%w %h", str(path)], text=True
    )
    return tuple(map(int, value.split()))  # type: ignore[return-value]


def resized_ppm(path: Path) -> tuple[int, int, bytes]:
    proc = subprocess.run(
        [
            "convert",
            str(path),
            "-background",
            "black",
            "-alpha",
            "remove",
            "-alpha",
            "off",
            "-resize",
            f"{MAX_SIDE}x{MAX_SIDE}>",
            "-depth",
            "8",
            "ppm:-",
        ],
        check=True,
        stdout=subprocess.PIPE,
    )
    data = proc.stdout
    match = re.match(rb"P6\s+(?:#[^\n]*\s+)*(\d+)\s+(\d+)\s+255\s", data)
    if not match:
        raise RuntimeError(f"PPM inesperado para {path.name}")
    width, height = map(int, match.groups())
    pixels = data[match.end() :]
    if len(pixels) != width * height * 3:
        raise RuntimeError(f"Tamaño PPM incorrecto para {path.name}")
    return width, height, pixels


def make_mask(pixels: bytes, layer: str) -> bytearray:
    mask = bytearray(len(pixels) // 3)
    out = 0
    for i in range(0, len(pixels), 3):
        r, g, b = pixels[i], pixels[i + 1], pixels[i + 2]
        if layer == "red":
            selected = r >= 132 and r >= g * 1.55 and r >= b * 1.55
        else:
            selected = r >= 152 and g >= 152 and b >= 152 and max(r, g, b) - min(r, g, b) < 42
        mask[out] = 1 if selected else 0
        out += 1
    return mask


def contours(mask: bytearray, width: int, height: int) -> list[list[tuple[int, int]]]:
    # Cada arista se orienta dejando la tinta a la derecha. Las islas y sus
    # huecos obtienen orientaciones opuestas y funcionan con fill-rule=evenodd.
    edges: dict[tuple[int, int], list[tuple[int, int]]] = {}

    def add(a: tuple[int, int], b: tuple[int, int]) -> None:
        edges.setdefault(a, []).append(b)

    for y in range(height):
        row = y * width
        for x in range(width):
            if not mask[row + x]:
                continue
            if y == 0 or not mask[row + x - width]:
                add((x, y), (x + 1, y))
            if x == width - 1 or not mask[row + x + 1]:
                add((x + 1, y), (x + 1, y + 1))
            if y == height - 1 or not mask[row + x + width]:
                add((x + 1, y + 1), (x, y + 1))
            if x == 0 or not mask[row + x - 1]:
                add((x, y + 1), (x, y))

    result: list[list[tuple[int, int]]] = []
    while edges:
        start = next(iter(edges))
        current = start
        previous: tuple[int, int] | None = None
        path = [start]
        for _ in range(sum(map(len, edges.values())) + 1):
            choices = edges.get(current)
            if not choices:
                break
            if len(choices) == 1 or previous is None:
                nxt = choices.pop()
            else:
                # En un contacto diagonal, continuar con el giro más cerrado
                # evita unir dos formas que solo comparten una esquina.
                vx, vy = current[0] - previous[0], current[1] - previous[1]
                nxt = max(
                    choices,
                    key=lambda q: (
                        vx * (q[1] - current[1]) - vy * (q[0] - current[0]),
                        vx * (q[0] - current[0]) + vy * (q[1] - current[1]),
                    ),
                )
                choices.remove(nxt)
            if not choices:
                del edges[current]
            previous, current = current, nxt
            if current == start:
                break
            path.append(current)
        if len(path) >= 4 and abs(polygon_area(path)) >= MIN_AREA:
            result.append(path)
    return result


def polygon_area(points: list[tuple[int, int]]) -> float:
    return 0.5 * sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1])
    )


def distance_to_segment(point, start, end) -> float:
    px, py = point
    ax, ay = start
    bx, by = end
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def rdp(points: list[tuple[int, int]], epsilon: float) -> list[tuple[int, int]]:
    if len(points) <= 2:
        return points
    start, end = points[0], points[-1]
    distance, index = max(
        (distance_to_segment(point, start, end), i)
        for i, point in enumerate(points[1:-1], 1)
    )
    if distance > epsilon:
        left = rdp(points[: index + 1], epsilon)
        right = rdp(points[index:], epsilon)
        return left[:-1] + right
    return [start, end]


def simplify_closed(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    # Se abre el anillo en dos puntos distantes para no colapsarlo al aplicar RDP.
    first = points[0]
    split = max(range(1, len(points)), key=lambda i: math.dist(first, points[i]))
    a = rdp(points[: split + 1], EPSILON)
    b = rdp(points[split:] + [first], EPSILON)
    return (a[:-1] + b[:-1]) or points


def path_data(shapes: list[list[tuple[int, int]]], sx: float, sy: float) -> str:
    chunks: list[str] = []
    for shape in shapes:
        points = simplify_closed(shape)
        coords = [(x * sx, y * sy) for x, y in points]
        first, *rest = coords
        chunk = [f"M{first[0]:.1f} {first[1]:.1f}"]
        chunk.extend(f"L{x:.1f} {y:.1f}" for x, y in rest)
        chunk.append("Z")
        chunks.append("".join(chunk))
    return "".join(chunks)


def vectorize(source: Path) -> Path:
    original_width, original_height = image_size(source)
    width, height, pixels = resized_ppm(source)
    scale_x, scale_y = original_width / width, original_height / height
    layers = []
    for name, color in (("red", "#ff0000"), ("white", "#ffffff")):
        shapes = contours(make_mask(pixels, name), width, height)
        if shapes:
            layers.append((name, color, path_data(shapes, scale_x, scale_y), len(shapes)))

    output = OUTPUT / f"{source.stem}.svg"
    layer_markup = "\n".join(
        f'  <path id="{name}" fill="{color}" fill-rule="evenodd" d="{data}"/>'
        for name, color, data, _ in layers
    )
    counts = ", ".join(f"{name}: {count}" for name, _, _, count in layers)
    output.write_text(
        f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {original_width} {original_height}" width="{original_width}" height="{original_height}">
  <title>{source.stem} — referencia vectorizada</title>
  <desc>Vectorización editable desde {source.name}. Capas: {counts}. Fondo transparente.</desc>
{layer_markup}
</svg>
'''
    )
    return output


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    for filename in SOURCES:
        source = ROOT / filename
        output = vectorize(source)
        print(f"{source.name} -> {output.relative_to(ROOT)} ({output.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
