import math
from tkinter.colorchooser import askcolor

from core.services.camera_light_service import (
    SPHERE_R,
    SPHERE_SIZE,
    angles_from_sphere_xy,
    blend_color,
    light_keyword,
    normalize_hemi_azimuth,
    sphere_xy_from_angles,
)
from shared.ui_kit import (
    BG_HOVER,
    FG_PRIMARY,
    ACCENT_BLUE,
    ACCENT_YELLOW,
    DARK_TEXT,
)


def draw_light_sphere(builder) -> None:
    canvas = builder._light_sphere_canvas
    if canvas is None:
        return
    canvas.delete("all")
    cx = cy = SPHERE_SIZE / 2
    r = SPHERE_R

    for i in range(4, 0, -1):
        rr = r * i / 4
        grey = 30 + i * 8
        col = f"#{grey:02x}{grey:02x}{grey+10:02x}"
        canvas.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline="", fill=col)

    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=BG_HOVER, width=1, fill="")

    for az_deg in range(0, 180, 45):
        points = []
        mirror_points = []
        for el_deg in range(-90, 91, 5):
            x, y = sphere_xy_from_angles(az_deg, el_deg)
            mx, my = sphere_xy_from_angles(-az_deg, el_deg)
            points.extend([x, y])
            mirror_points.extend([mx, my])
        if len(points) >= 4:
            canvas.create_line(points, fill="#2a2a4a", width=1, smooth=True)
        if len(mirror_points) >= 4:
            canvas.create_line(mirror_points, fill="#2a2a4a", width=1, smooth=True)

    for el_deg in [-60, -30, 0, 30, 60]:
        _, yy = sphere_xy_from_angles(0, el_deg)
        ry = r * math.cos(math.radians(el_deg))
        col = "#3a3a5a" if el_deg != 0 else "#4a4a6a"
        canvas.create_oval(cx - ry, yy - ry * 0.15, cx + ry, yy + ry * 0.15, outline=col, width=1, fill="")

    canvas.create_oval(cx - r, cy - r * 0.15, cx + r, cy + r * 0.15, outline="#55557a", width=1, fill="")

    lx, ly = sphere_xy_from_angles(builder.light_azimuth.get(), builder.light_elevation.get())
    canvas.create_line(cx, cy, lx, ly, fill=ACCENT_YELLOW, width=1, dash=(3, 3))

    dot_r = 7
    color = builder.light_color or "#ffffff"
    for halo in [14, 10]:
        alpha_col = blend_color(color, "#1a1a2e", halo / 14)
        canvas.create_oval(lx - halo, ly - halo, lx + halo, ly + halo, outline="", fill=alpha_col)
    canvas.create_oval(lx - dot_r, ly - dot_r, lx + dot_r, ly + dot_r,
                       outline="#ffffff", width=1, fill=color, tags="dot")
    builder._light_dot_id = "dot"


def sphere_click(builder, event) -> None:
    azimuth, elevation = angles_from_sphere_xy(
        event.x,
        event.y,
        current_azimuth=builder.light_azimuth.get(),
        back_mode=builder.light_back_mode.get(),
    )
    builder.light_azimuth.set(round(azimuth, 1))
    builder.light_elevation.set(round(elevation, 1))
    draw_light_sphere(builder)
    update_light_labels(builder)
    builder._generate()


def sphere_drag(builder, event) -> None:
    sphere_click(builder, event)


def sphere_release(builder, event) -> None:
    sphere_click(builder, event)


def update_light_labels(builder) -> None:
    azimuth = builder.light_azimuth.get()
    elevation = builder.light_elevation.get()
    if builder._azimuth_label:
        builder._azimuth_label.config(text=f"水平角: {azimuth:.0f}°")
    if builder._elev_label:
        builder._elev_label.config(text=f"仰俯角: {elevation:.0f}°")
    if builder._light_kw_label:
        builder._light_kw_label.config(text=light_keyword(azimuth, elevation, builder.light_color))


def pick_light_color(builder) -> None:
    result = askcolor(color=builder.light_color, parent=builder, title="选择光源颜色")
    if not result or not result[1]:
        return
    builder.light_color = result[1].lower()
    if builder._light_color_btn:
        builder._light_color_btn.config(bg=builder.light_color, activebackground=builder.light_color)
    if builder._light_color_label:
        builder._light_color_label.config(text=builder.light_color)
    draw_light_sphere(builder)
    update_light_labels(builder)
    builder._generate()


def set_hemi(builder, back: bool) -> None:
    builder.light_back_mode.set(back)
    if builder._hemi_front_btn:
        builder._hemi_front_btn.config(
            bg=ACCENT_BLUE if not back else BG_HOVER,
            fg=DARK_TEXT if not back else FG_PRIMARY,
        )
    if builder._hemi_back_btn:
        builder._hemi_back_btn.config(
            bg=ACCENT_BLUE if back else BG_HOVER,
            fg=DARK_TEXT if back else FG_PRIMARY,
        )
    builder.light_azimuth.set(normalize_hemi_azimuth(builder.light_azimuth.get(), back=back))
    draw_light_sphere(builder)
    update_light_labels(builder)
    builder._generate()


def toggle_rim_light(builder) -> None:
    builder.rim_light_var.set(not builder.rim_light_var.get())
    on = builder.rim_light_var.get()
    builder._rim_btn.config(
        text="● 开" if on else "○ 关",
        bg=ACCENT_YELLOW if on else BG_HOVER,
        fg=DARK_TEXT if on else FG_PRIMARY,
    )
    builder._generate()
