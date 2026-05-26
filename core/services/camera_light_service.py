import colorsys
import math


SPHERE_R = 68
SPHERE_SIZE = 160


def sphere_xy_from_angles(
    azimuth: float,
    elevation: float,
    *,
    radius: float = SPHERE_R,
    size: float = SPHERE_SIZE,
) -> tuple[float, float]:
    cx = cy = size / 2
    az = math.radians(azimuth)
    el = math.radians(elevation)
    x = cx + radius * math.sin(az) * math.cos(el)
    y = cy - radius * math.sin(el)
    return x, y


def angles_from_sphere_xy(
    mx: float,
    my: float,
    *,
    current_azimuth: float,
    back_mode: bool,
    radius: float = SPHERE_R,
    size: float = SPHERE_SIZE,
) -> tuple[float, float]:
    cx = cy = size / 2
    dx = mx - cx
    dy = -(my - cy)
    dist = math.hypot(dx, dy)
    if dist > radius:
        scale = radius / dist
        dx *= scale
        dy *= scale
    elevation = math.degrees(math.asin(max(-1, min(1, dy / radius))))
    cos_el = math.cos(math.radians(elevation))
    if cos_el <= 1e-6:
        return current_azimuth, elevation

    sin_az = max(-1.0, min(1.0, dx / (radius * cos_el)))
    az_raw = math.degrees(math.asin(sin_az))
    azimuth = (180.0 - az_raw) % 360 if back_mode else az_raw % 360
    return azimuth, elevation


def normalize_hemi_azimuth(azimuth: float, *, back: bool) -> float:
    if back and not (90 <= azimuth <= 270):
        return (180 - azimuth) % 360
    if not back and (90 < azimuth < 270):
        return (180 - azimuth) % 360
    return azimuth


def blend_color(hex1: str, hex2: str, t: float) -> str:
    def parse(value: str) -> tuple[int, int, int]:
        value = value.lstrip("#")
        return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)

    r1, g1, b1 = parse(hex1)
    r2, g2, b2 = parse(hex2)
    return f"#{int(r1*t+r2*(1-t)):02x}{int(g1*t+g2*(1-t)):02x}{int(b1*t+b2*(1-t)):02x}"


def light_keyword(azimuth: float, elevation: float, color: str) -> str:
    direction = _direction_keyword(azimuth % 360, elevation)
    color_name = _color_keyword(color)
    if color_name in {"white", "warm white"}:
        return direction
    return f"{color_name} {direction}"


def _direction_keyword(azimuth: float, elevation: float) -> str:
    if elevation > 60:
        return "overhead top-down lighting"
    if elevation < -60:
        return "underlighting from below"

    sectors = [
        (0, 22, "front lighting"),
        (22, 68, "front-right lighting"),
        (68, 112, "right side lighting"),
        (112, 158, "back-right lighting"),
        (158, 202, "back lighting"),
        (202, 248, "back-left lighting"),
        (248, 292, "left side lighting"),
        (292, 338, "front-left lighting"),
        (338, 360, "front lighting"),
    ]
    direction = "front lighting"
    for lo, hi, name in sectors:
        if lo <= azimuth < hi:
            direction = name
            break
    if elevation > 30:
        return "high " + direction
    if elevation < -15:
        return "low " + direction
    return direction


def _color_keyword(color: str) -> str:
    color = (color or "#ffffff").lower()
    color_map = {
        "#ffffff": "white",
        "#fff4e0": "warm white",
        "#ffd700": "golden",
        "#ff8c00": "orange",
        "#ff4500": "red-orange",
        "#ff0000": "red",
        "#ff69b4": "pink",
        "#00bfff": "cool blue",
        "#87ceeb": "soft blue",
        "#00ffff": "cyan",
        "#00ff00": "green",
        "#9400d3": "purple",
    }
    if color in color_map:
        return color_map[color]

    def hex_to_rgb(value: str) -> tuple[float, float, float]:
        value = value.lstrip("#")
        return int(value[0:2], 16) / 255, int(value[2:4], 16) / 255, int(value[4:6], 16) / 255

    def color_dist(left: str, right: str) -> float:
        r1, g1, b1 = hex_to_rgb(left)
        r2, g2, b2 = hex_to_rgb(right)
        return (r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2

    best = min(color_map.keys(), key=lambda key: color_dist(key, color))
    if color_dist(best, color) < 0.15:
        return color_map[best]

    r, g, b = hex_to_rgb(color)
    hue, saturation, value = colorsys.rgb_to_hsv(r, g, b)
    if saturation < 0.15:
        return "white" if value > 0.8 else "grey"
    hue_names = [
        (0, "red"),
        (30 / 360, "orange"),
        (60 / 360, "yellow"),
        (120 / 360, "green"),
        (180 / 360, "cyan"),
        (240 / 360, "blue"),
        (300 / 360, "purple"),
        (330 / 360, "pink"),
        (1.0, "red"),
    ]
    return min(hue_names, key=lambda item: abs(item[0] - hue))[1]
