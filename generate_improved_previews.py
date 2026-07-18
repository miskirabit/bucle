#!/usr/bin/env python3
"""
Improved boca configurator preview generator.
Generates accurate SVG + PNG using the fixed mouth/teeth logic.
Uses ImageMagick (convert) for reliable PNG rendering.
"""

import math
import subprocess
import os
import tempfile

def generate_mouth_path(cx, cy, w, h, lip_thick, upper_c, lower_c, smile):
    half_w = w / 2.0
    smile_factor = smile / 75.0
    thickness = max(10.0, lip_thick)

    # OUTER LIP (red)
    outer_top_y = cy - (h * upper_c) + (smile_factor * 14)
    outer_bottom_y = cy + (h * lower_c) + (smile_factor * -18)

    outer_left = cx - half_w
    outer_right = cx + half_w

    outer_top_ctrl_x1 = cx - half_w * 0.52
    outer_top_ctrl_y1 = cy - (h * upper_c * 1.08) + smile * 0.28
    outer_top_ctrl_x2 = cx + half_w * 0.52
    outer_top_ctrl_y2 = outer_top_ctrl_y1

    outer_bot_ctrl_x1 = cx - half_w * 0.58
    outer_bot_ctrl_y1 = cy + (h * lower_c * 1.02) + smile * -0.38
    outer_bot_ctrl_x2 = cx + half_w * 0.58
    outer_bot_ctrl_y2 = outer_bot_ctrl_y1

    outer = (
        f"M {outer_left:.1f} {cy} "
        f"Q {outer_top_ctrl_x1:.1f} {outer_top_y:.1f} {cx} {outer_top_y - 4:.1f} "
        f"Q {outer_top_ctrl_x2:.1f} {outer_top_y:.1f} {outer_right:.1f} {cy} "
        f"Q {outer_bot_ctrl_x2:.1f} {outer_bottom_y:.1f} {cx} {outer_bottom_y + 3:.1f} "
        f"Q {outer_bot_ctrl_x1:.1f} {outer_bottom_y:.1f} {outer_left:.1f} {cy} Z"
    )

    # INNER (black opening)
    inset = thickness * 0.75
    inner_w = w * (0.82 - (thickness / 420.0))
    inner_h = h * (0.68 - (thickness / 520.0))
    inner_half = inner_w / 2.0

    inner_left = cx - inner_half
    inner_right = cx + inner_half

    inner_top = cy - (inner_h * upper_c) + (smile_factor * 8) + inset * 0.3
    inner_bottom = cy + (inner_h * lower_c) + (smile_factor * -12) - inset * 0.5

    inner_top_ctrl_x1 = cx - inner_half * 0.48
    inner_top_ctrl_y1 = inner_top + (inset * 0.15)
    inner_top_ctrl_x2 = cx + inner_half * 0.48
    inner_top_ctrl_y2 = inner_top_ctrl_y1

    inner_bot_ctrl_x1 = cx - inner_half * 0.52
    inner_bot_ctrl_y1 = inner_bottom - (inset * 0.2)
    inner_bot_ctrl_x2 = cx + inner_half * 0.52
    inner_bot_ctrl_y2 = inner_bot_ctrl_y1

    inner = (
        f"M {inner_left:.1f} {cy} "
        f"Q {inner_top_ctrl_x1:.1f} {inner_top:.1f} {cx} {inner_top:.1f} "
        f"Q {inner_top_ctrl_x2:.1f} {inner_top:.1f} {inner_right:.1f} {cy} "
        f"Q {inner_bot_ctrl_x2:.1f} {inner_bottom:.1f} {cx} {inner_bottom:.1f} "
        f"Q {inner_bot_ctrl_x1:.1f} {inner_bottom:.1f} {inner_left:.1f} {cy} Z"
    )

    inner_bounds = {
        'left': inner_left,
        'right': inner_right,
        'top': inner_top,
        'bottom': inner_bottom,
        'center_y': (inner_top + inner_bottom) / 2,
        'height': inner_bottom - inner_top
    }

    return outer, inner, inner_bounds


def generate_teeth(inner_bounds, count, tw, th, spacing, style, offset_y):
    if not inner_bounds:
        return [], None

    mouth_w = inner_bounds['right'] - inner_bounds['left']
    cx = (inner_bounds['left'] + inner_bounds['right']) / 2

    scale = max(0.6, min(1.4, mouth_w / 310.0))
    tooth_w = tw * scale
    tooth_h = th * scale

    total_w = (tooth_w + spacing) * count - spacing
    start_x = cx - total_w / 2

    base_y = inner_bounds['center_y'] + offset_y + (inner_bounds['height'] * 0.08)
    teeth_bottom_line = base_y + tooth_h * 0.92

    teeth = []
    max_h = inner_bounds['bottom'] - base_y - 2

    for i in range(count):
        x = start_x + i * (tooth_w + spacing) + (tooth_w / 2)

        hmod = min(tooth_h, max_h)
        wmod = tooth_w

        if style == 'pointed':
            hmod = min(hmod * (1 + (i % 2) * 0.18), max_h)
            ty = base_y + hmod * 0.95
            p = f"M {x - wmod/2:.1f} {base_y:.1f} L {x:.1f} {ty:.1f} L {x + wmod/2:.1f} {base_y:.1f} Z"
        elif style == 'fangs':
            if i in (0, count-1):
                hmod = min(hmod * 1.42, max_h * 1.05)
            elif i in (1, count-2):
                hmod = min(hmod * 1.12, max_h)
            ty = base_y + hmod * 0.96
            side = wmod * 0.42
            p = f"M {x - side:.1f} {base_y:.1f} L {x:.1f} {ty:.1f} L {x + side:.1f} {base_y:.1f} Z"
        elif style == 'bat':
            mod = math.sin(i * 1.25) * 0.28
            hmod = min(hmod * (0.82 + mod), max_h)
            wmod = tooth_w * (0.92 + math.cos(i * 0.9) * 0.14)
            p1y = base_y + hmod * 0.38
            p2y = base_y + hmod * 0.88
            p = (f"M {x - wmod/2:.1f} {base_y:.1f} "
                 f"Q {x - wmod/2.1:.1f} {p1y:.1f} {x - wmod * 0.12:.1f} {p2y:.1f} "
                 f"Q {x:.1f} {p2y + 3:.1f} {x + wmod * 0.12:.1f} {p2y:.1f} "
                 f"Q {x + wmod/2.1:.1f} {p1y:.1f} {x + wmod/2:.1f} {base_y:.1f} Z")
        elif style == 'square':
            wmod = tooth_w * 1.08
            hmod = min(hmod * 0.82, max_h)
            by = base_y + hmod
            p = f"M {x - wmod/2:.1f} {base_y:.1f} L {x + wmod/2:.1f} {base_y:.1f} L {x + wmod/2:.1f} {by:.1f} L {x - wmod/2:.1f} {by:.1f} Z"
        else:  # straight
            hmod = min(hmod, max_h)
            by = base_y + hmod
            rnd = min(6.0, wmod * 0.18)
            p = (f"M {x - wmod/2:.1f} {base_y:.1f} "
                 f"L {x + wmod/2:.1f} {base_y:.1f} "
                 f"L {x + wmod/2:.1f} {by - rnd:.1f} "
                 f"Q {x + wmod/2:.1f} {by:.1f} {x + wmod/2 - rnd:.1f} {by:.1f} "
                 f"L {x - wmod/2 + rnd:.1f} {by:.1f} "
                 f"Q {x - wmod/2:.1f} {by:.1f} {x - wmod/2:.1f} {by - rnd:.1f} Z")
        teeth.append(p.strip())

    return teeth, teeth_bottom_line


def build_svg(params, view_w=620, view_h=460):
    cx, cy = 310, 235

    outer, inner, bounds = generate_mouth_path(
        cx, cy,
        params['mouthWidth'], params['mouthHeight'],
        params['lipThickness'],
        params['upperCurve'], params['lowerCurve'],
        params['smile']
    )

    teeth, teeth_bottom = generate_teeth(
        bounds,
        params['teethCount'],
        params['toothWidth'], params['toothHeight'],
        params['toothSpacing'],
        params['teethStyle'],
        params['teethY']
    )

    parts = [
        f'<?xml version="1.0" encoding="UTF-8"?>\n',
        f'<svg width="{view_w}" height="{view_h}" viewBox="0 0 {view_w} {view_h}" xmlns="http://www.w3.org/2000/svg">\n',
        '  <rect width="100%" height="100%" fill="#0a0a0c"/>\n'
    ]

    if params.get('show_boca', True):
        parts.append(f'  <path d="{outer}" fill="{params["mouthColor"]}"/>\n')
        parts.append(f'  <path d="{inner}" fill="#111111"/>\n')

    if params.get('show_teeth', True) and teeth:
        for t in teeth:
            parts.append(f'  <path d="{t}" fill="{params["teethColor"]}"/>\n')

        if teeth_bottom and bounds:
            left = bounds['left'] + 8
            right = bounds['right'] - 8
            ly = teeth_bottom
            parts.append(f'  <path d="M {left:.1f} {ly:.1f} Q {cx} {ly + 6:.1f} {right:.1f} {ly:.1f}" fill="none" stroke="#f8f8f8" stroke-width="3.5" opacity="0.75"/>\n')
            parts.append(f'  <path d="M {left:.1f} {ly:.1f} Q {cx} {ly + 3:.1f} {right:.1f} {ly:.1f}" fill="none" stroke="#ddd" stroke-width="1.8" opacity="0.9"/>\n')

    parts.append('</svg>')
    return ''.join(parts)


def render_svg_to_png(svg_str, png_path, width=620):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(svg_str)
        svg_file = f.name

    try:
        # Use ImageMagick convert (reliable here)
        cmd = [
            'convert',
            '-background', 'none',
            '-density', '150',
            svg_file,
            '-resize', f'{width}x',
            png_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print("convert stderr:", result.stderr)
            return False
        return True
    finally:
        try:
            os.unlink(svg_file)
        except:
            pass


if __name__ == "__main__":
    os.makedirs('/home/user/bucle/previews', exist_ok=True)

    base = {
        "mouthWidth": 380,
        "mouthHeight": 135,
        "lipThickness": 28,
        "upperCurve": 0.75,
        "lowerCurve": 1.05,
        "smile": 0,
        "mouthColor": "#ff2d55",
        "teethCount": 8,
        "toothWidth": 34,
        "toothHeight": 52,
        "toothSpacing": 6,
        "teethY": 0,
        "teethColor": "#ffffff",
        "teethStyle": "straight",
        "show_boca": True,
        "show_teeth": True,
    }

    configs = [
        ("default", base),
        ("smile", {**base, "smile": 42, "mouthHeight": 105, "mouthWidth": 420, "teethCount": 9, "teethStyle": "pointed"}),
        ("open", {**base, "mouthHeight": 195, "lipThickness": 22, "smile": -8, "teethStyle": "straight", "teethY": 4}),
        ("fangs", {**base, "teethCount": 7, "teethStyle": "fangs", "teethY": 8, "toothHeight": 68, "smile": -10}),
        ("bat", {**base, "teethCount": 10, "teethStyle": "bat", "mouthWidth": 395, "smile": 22}),
        ("closed", {**base, "mouthHeight": 62, "lipThickness": 36, "smile": 12, "teethCount": 6}),
    ]

    for name, p in configs:
        svg = build_svg(p)
        svg_path = f"/home/user/bucle/previews/{name}.svg"
        with open(svg_path, "w") as f:
            f.write(svg)

        png_path = f"/home/user/bucle/previews/{name}.png"
        ok = render_svg_to_png(svg, png_path, width=620)
        if ok:
            print(f"✓ Generated {png_path}")
        else:
            print(f"✗ Failed to render {name}")

    print("\nPreviews saved to /home/user/bucle/previews/")