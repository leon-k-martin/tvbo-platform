#!/usr/bin/env python
"""Bake the world map that live survey sessions draw country answers on.

Reads the Natural Earth admin-0 countries (the 110m outlines for the land, the 50m label points so that small states such as Singapore or Malta still get an anchor), projects them with the Equal Earth projection and writes ``odoo-addons/tvbo/static/src/img/world_map.svg``. Every outline is a ``<path data-code="DE">`` and every anchor a ``<circle data-code="DE">`` keyed by the ISO 3166-1 alpha-2 code that ``res.country.code`` uses; Antarctica is left out.

Run from the repo root once, the SVG is committed::

    curl -sSfLO https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_110m_admin_0_countries.geojson
    curl -sSfLO https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_50m_admin_0_countries.geojson
    python scripts/build_world_map.py ne_110m_admin_0_countries.geojson ne_50m_admin_0_countries.geojson
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'odoo-addons/tvbo/static/src/img/world_map.svg'
WIDTH = 1000
A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
# Equal Earth spans x in [-2.7064, 2.7064] and y in [-1.3173, 1.3173] for unit radius.
X_MAX, Y_MAX = 2.7064, 1.3173
Y_CUT = -60.0


def project(lon: float, lat: float) -> tuple[float, float]:
    """Equal Earth projection (Šavrič et al. 2018) scaled to the SVG canvas."""
    lam, phi = math.radians(lon), math.radians(lat)
    theta = math.asin(math.sqrt(3) / 2 * math.sin(phi))
    t2, t6 = theta ** 2, theta ** 6
    x = 2 * math.sqrt(3) * lam * math.cos(theta) / (3 * (9 * A4 * t6 * t2 + 7 * A3 * t6 + 3 * A2 * t2 + A1))
    y = theta * (A4 * t6 * t2 + A3 * t6 + A2 * t2 + A1)
    scale = WIDTH / (2 * X_MAX)
    return (x + X_MAX) * scale, (Y_MAX - y) * scale


def iso2(props: dict) -> str | None:
    """ISO alpha-2 code, preferring the ``_EH`` column that fills France, Norway and Kosovo."""
    code = props.get('ISO_A2_EH') or props.get('ISO_A2')
    return code if code and code != '-99' else None


def ring_path(ring: list) -> str:
    """One closed SVG subpath, dropping vertices that land on the previous pixel tenth."""
    points, last = [], None
    for lon, lat in ring:
        x, y = project(lon, lat)
        point = (round(x, 1), round(y, 1))
        if point != last:
            points.append(point)
            last = point
    if len(points) < 3:
        return ''
    return 'M' + 'L'.join(f'{x:g},{y:g}' for x, y in points) + 'Z'


def outline(geometry: dict) -> str:
    polygons = geometry['coordinates'] if geometry['type'] == 'MultiPolygon' else [geometry['coordinates']]
    return ''.join(ring_path(ring) for polygon in polygons for ring in polygon)


def main(outlines_file: str, anchors_file: str) -> None:
    paths, anchors = [], {}
    for feature in json.loads(Path(outlines_file).read_text())['features']:
        props = feature['properties']
        code = iso2(props)
        if props.get('CONTINENT') == 'Antarctica':
            continue
        d = outline(feature['geometry'])
        paths.append(f'<path d="{d}"' + (f' data-code="{code}"' if code else '') + '/>')
    for feature in json.loads(Path(anchors_file).read_text())['features']:
        props = feature['properties']
        code = iso2(props)
        if code and code not in anchors and props['LABEL_Y'] > Y_CUT:
            x, y = project(props['LABEL_X'], props['LABEL_Y'])
            anchors[code] = f'<circle data-code="{code}" cx="{x:.1f}" cy="{y:.1f}" r="0"/>'
    top, bottom = project(0, 84)[1], project(0, Y_CUT)[1]
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {top:.1f} {WIDTH} {bottom - top:.1f}" class="o_tvbo_world_map">'
        f'<g class="o_tvbo_world_land">{"".join(paths)}</g>'
        f'<g class="o_tvbo_world_anchors">{"".join(anchors[c] for c in sorted(anchors))}</g>'
        '</svg>\n'
    )
    OUT.write_text(svg)
    print(f'{OUT}: {len(paths)} outlines, {len(anchors)} anchors, {len(svg) / 1024:.0f} KiB')


if __name__ == '__main__':
    main(*sys.argv[1:3])
