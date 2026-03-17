#!/usr/bin/env python3
"""
svg_to_curves.py

Convert SVG paths into the plain-text Bezier curve format used by the
Beziers3D simulator.

The simulator expects curves defined as:

<num_curves>
<num_points_curve0>
x y z
x y z
...
<num_points_curve1>
x y z
...

Where:
• Each curve is defined by its control points
• Coordinates are in 3D space

This script converts SVG segments into cubic Bezier curves and places
them on the simulator grid (XZ plane).

Usage:
    ./svg_to_curves.py input.svg output.txt
"""

from svgpathtools import svg2paths, CubicBezier, Line, QuadraticBezier, Arc
import argparse
from typing import List, Tuple


# ------------------------------------------------------------
# Conversion helpers
# ------------------------------------------------------------

def quad_to_cubic(q: QuadraticBezier) -> CubicBezier:
    """
    Convert a quadratic Bezier to an equivalent cubic Bezier.
    """
    p0, p1, p2 = q.start, q.control, q.end

    c1 = p0 + (2/3) * (p1 - p0)
    c2 = p2 + (2/3) * (p1 - p2)

    return CubicBezier(p0, c1, c2, p2)


def line_to_cubic(l: Line) -> CubicBezier:
    """
    Convert a line segment into a cubic Bezier curve.
    """
    p0, p3 = l.start, l.end

    c1 = p0 + (p3 - p0) / 3
    c2 = p0 + 2 * (p3 - p0) / 3

    return CubicBezier(p0, c1, c2, p3)


def arc_to_cubics(a: Arc):
    """
    Convert an SVG arc into multiple cubic Bezier curves.
    """
    return a.as_cubic_curves()


# ------------------------------------------------------------
# Coordinate transform
# ------------------------------------------------------------

def transform(x: float, y: float, scale: float = 0.05, flip_y: bool = False) -> Tuple[float, float]:
    """
    Convert SVG coordinates into simulator coordinates.

    SVG space:
        X → right
        Y → down

    Simulator space:
        X → right
        Z → forward
        Y → up

    We map:
        SVG X → simulator X
        SVG Y → simulator Z
        simulator Y = 0 (placed on the grid)

    flip_y is enabled because SVG Y grows downward.
    """

    if flip_y:
        y = -y

    return x * scale, y * scale


# ------------------------------------------------------------
# Curve utilities
# ------------------------------------------------------------

def cubic_length(b: CubicBezier) -> float:
    """
    Approximate length of a cubic curve using control polygon.
    Used to discard very small segments.
    """

    pts = [b.start, b.control1, b.control2, b.end]

    return sum(abs(pts[i + 1] - pts[i]) for i in range(3))


# ------------------------------------------------------------
# SVG → curve conversion
# ------------------------------------------------------------

def convert(svgfile: str) -> List[List[Tuple[float, float, float]]]:
    """
    Parse an SVG file and return curves in simulator format.

    Returns:
        List of curves
        Each curve = list of (x, y, z) control points
    """

    paths, _ = svg2paths(svgfile)

    all_curves: List[List[Tuple[float, float, float]]] = []

    for path in paths:
        for seg in path:

            # Normalize all segments to cubic Beziers
            if isinstance(seg, CubicBezier):
                beziers = [seg]

            elif isinstance(seg, QuadraticBezier):
                beziers = [quad_to_cubic(seg)]

            elif isinstance(seg, Line):
                beziers = [line_to_cubic(seg)]

            elif isinstance(seg, Arc):
                beziers = arc_to_cubics(seg)

            else:
                continue

            for b in beziers:

                # Skip degenerate curves
                if abs(b.start - b.end) < 1e-6:
                    continue

                if cubic_length(b) < 1e-5:
                    continue

                pts = [b.start, b.control1, b.control2, b.end]

                control_points: List[Tuple[float, float, float]] = []

                for p in pts:

                    x, z = transform(p.real, p.imag)

                    # Place curve on grid (y = 0)
                    point = (x - 20.0, 0.0, z - 25.0)

                    # Avoid inserting duplicate consecutive points
                    if not control_points or control_points[-1] != point:
                        control_points.append(point)

                if len(control_points) < 2:
                    continue

                all_curves.append(control_points)

    return all_curves

def center_curves(curves: List[List[Tuple[float, float, float]]]):
    """
    Center all curves around the origin in the XZ plane.
    """

    xs = []
    zs = []

    for curve in curves:
        for x, y, z in curve:
            xs.append(x)
            zs.append(z)

    min_x, max_x = min(xs), max(xs)
    min_z, max_z = min(zs), max(zs)

    center_x = (min_x + max_x) / 2
    center_z = (min_z + max_z) / 2

    centered = []

    for curve in curves:
        new_curve = []
        for x, y, z in curve:
            new_curve.append((x - center_x, y, z - center_z))
        centered.append(new_curve)

    return centered


# ------------------------------------------------------------
# File writer
# ------------------------------------------------------------

def write_curves_txt(curves: List[List[Tuple[float, float, float]]], out_filename: str) -> None:
    """
    Write curves to the simulator text format.
    """

    with open(out_filename, "w", encoding="utf-8") as f:

        # Number of curves
        f.write(f"{len(curves)}\n")

        for curve in curves:

            # Number of control points
            f.write(f"{len(curve)}\n")

            for (x, y, z) in curve:

                f.write(f"{x:.6f} {y:.6f} {z:.6f}\n")


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description="Convert SVG paths into Beziers3D curve format"
    )

    parser.add_argument("input_svg", help="Input SVG file")
    parser.add_argument("output_txt", help="Output curves file")

    args = parser.parse_args()

    curves = convert(args.input_svg)
    curves = center_curves(curves)

    if not curves:
        print("Warning: No valid curves found.")

    write_curves_txt(curves, args.output_txt)

    print(f"✓ Wrote {len(curves)} curve(s) to '{args.output_txt}'")


if __name__ == "__main__":
    main()