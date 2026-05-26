from core.services.camera_light_service import (
    angles_from_sphere_xy,
    blend_color,
    light_keyword,
    normalize_hemi_azimuth,
    sphere_xy_from_angles,
)


def test_light_keyword_describes_direction_and_ignores_white_color():
    assert light_keyword(45, 0, "#ffffff") == "front-right lighting"
    assert light_keyword(90, 35, "#ff0000") == "red high right side lighting"


def test_light_keyword_maps_nearest_or_hue_color():
    assert light_keyword(180, 0, "#ff7f00") == "orange back lighting"
    assert light_keyword(0, 0, "#111111") == "grey front lighting"


def test_sphere_coordinate_round_trip_front_side():
    x, y = sphere_xy_from_angles(45, 30)
    az, el = angles_from_sphere_xy(x, y, current_azimuth=0, back_mode=False)

    assert round(az, 1) == 45.0
    assert round(el, 1) == 30.0


def test_sphere_coordinate_respects_back_hemisphere():
    x, y = sphere_xy_from_angles(135, 0)
    az, el = angles_from_sphere_xy(x, y, current_azimuth=0, back_mode=True)

    assert round(az, 1) == 135.0
    assert round(el, 1) == 0.0


def test_normalize_hemi_azimuth_mirrors_out_of_range_angles():
    assert normalize_hemi_azimuth(45, back=True) == 135
    assert normalize_hemi_azimuth(135, back=False) == 45
    assert normalize_hemi_azimuth(180, back=True) == 180


def test_blend_color():
    assert blend_color("#ffffff", "#000000", 0.5) == "#7f7f7f"
