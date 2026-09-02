from shared import qt_compat as tk

from core.services.camera_light_service import light_keyword
from core.services.camera_prompt_service import (
    CameraPromptSpec,
    build_camera_prompt,
    build_detail_tech_zh as build_detail_tech_zh_text,
    build_negative_zh as build_negative_zh_text,
    build_prompt_zh as build_prompt_zh_text,
    build_style_mood_zh as build_style_mood_zh_text,
    build_subject_scene_zh,
)
from features.camera_builder.presets import (
    AESTHETIC_ANIME,
    AESTHETIC_REAL,
    CAMERA_ELEVATION,
    COLOR_SUPPLEMENT_ANIME,
    COLOR_SUPPLEMENT_REAL,
    MOOD_ANIME,
    MOOD_REAL,
    NEGATIVE_ZH_MAP,
    PARAMS_ANIME,
    PARAMS_REAL,
    QUALITY_CHIPS_ANIME,
    QUALITY_CHIPS_REAL,
    SHOT_SCALE,
    STYLE_ANIME,
    STYLE_REAL,
    SUBJECT_ANGLE,
    TEXTURE_ANIME,
    TEXTURE_REAL,
)
from shared.constants import ZH_PARAM_NAMES, kw_to_zh


class CameraBuilderStateCollector:
    def __init__(self, builder):
        self.builder = builder

    def build_prompt(self) -> str:
        b = self.builder
        subject = self._text_value(b.subject_text, b._SUBJECT_HINT)
        environment = self._text_value(b.environ_text, b._ENVIRON_HINT)

        parameters = []
        params = PARAMS_ANIME if b.is_anime.get() else PARAMS_REAL
        for name, (_, kw_fn) in params.items():
            if not b.param_checks.get(name, tk.BooleanVar(value=False)).get():
                continue
            custom_val = b.custom_vars.get(name, tk.StringVar()).get().strip()
            if custom_val and custom_val != "自定义...":
                kw = custom_val
            else:
                selected_val = b.param_vars.get(name, tk.StringVar()).get()
                kw = kw_fn(selected_val)
            if kw:
                parameters.append(kw)

        return build_camera_prompt(CameraPromptSpec(
            subject=subject,
            environment=environment,
            parameters=parameters,
            camera_terms=self._camera_terms(),
            filters=self._active_filter_terms(),
            style_terms=self._style_terms(),
            detail_terms=self._detail_terms(),
            render=b.render_var.get().strip(),
            ratio=b.ratio_var.get().strip(),
            extra=b.extra_var.get().strip(),
        ))

    def build_prompt_zh(self) -> str:
        b = self.builder
        return build_prompt_zh_text(
            mode="二次元" if b.is_anime.get() else "实拍",
            subject_scene=self.build_subject_scene_zh(),
            params=self._param_zh_lines(),
            camera=self._camera_zh_lines(),
            filters=[kw_to_zh(value) for value in self._active_filter_terms()],
            style_mood=self.build_style_mood_zh(),
            detail_tech=self.build_detail_tech_zh(),
            extra=b.extra_var.get().strip(),
        )

    def build_negative_zh(self, negative_text: str) -> str:
        return build_negative_zh_text(negative_text, NEGATIVE_ZH_MAP, kw_to_zh)

    def negative_text(self) -> str:
        b = self.builder
        return b.neg_text.get("1.0", tk.END).strip() if b.neg_text is not None else ""

    def build_subject_scene_zh(self) -> str:
        b = self.builder
        return build_subject_scene_zh(
            self._text_value(b.subject_text, b._SUBJECT_HINT),
            self._text_value(b.environ_text, b._ENVIRON_HINT),
        )

    def build_style_mood_zh(self) -> str:
        b = self.builder
        is_anime = b.is_anime.get()
        return build_style_mood_zh_text(
            styles=[kw for kw, bv in b.style_toggles.items() if bv.get()],
            aesthetics=[kw for kw, bv in b.aesthetic_toggles.items() if bv.get()],
            moods=[kw for kw, bv in b.mood_toggles.items() if bv.get()],
            motion=b.motion_var.get().strip(),
            style_map={kw: zh for kw, zh in (STYLE_ANIME if is_anime else STYLE_REAL)},
            aesthetic_map={kw: zh for kw, zh in (AESTHETIC_ANIME if is_anime else AESTHETIC_REAL)},
            mood_map={kw: zh for kw, zh in (MOOD_ANIME if is_anime else MOOD_REAL)},
            fallback=kw_to_zh,
        )

    def build_detail_tech_zh(self) -> str:
        b = self.builder
        is_anime = b.is_anime.get()
        return build_detail_tech_zh_text(
            qualities=[kw for kw, bv in b.quality_toggles.items() if bv.get()],
            textures=[kw for kw, bv in b.texture_toggles.items() if bv.get()],
            colors=[kw for kw, bv in b.color_toggles.items() if bv.get()],
            render=b.render_var.get().strip(),
            ratio=b.ratio_var.get().strip(),
            quality_map={kw: zh for kw, zh in (QUALITY_CHIPS_ANIME if is_anime else QUALITY_CHIPS_REAL)},
            texture_map={kw: zh for kw, zh in (TEXTURE_ANIME if is_anime else TEXTURE_REAL)},
            color_map={kw: zh for kw, zh in (COLOR_SUPPLEMENT_ANIME if is_anime else COLOR_SUPPLEMENT_REAL)},
        )

    def _camera_terms(self) -> list[str]:
        b = self.builder
        terms = []
        if b.shot_enabled.get():
            terms.append(SHOT_SCALE[b.shot_var.get()][0])
        if b.elevation_enabled.get():
            terms.append(CAMERA_ELEVATION[b.elevation_var.get()][0])
        if b.subject_angle_enabled.get():
            terms.append(SUBJECT_ANGLE[b.subject_angle_var.get()][0])
        if b.light_dir_enabled.get():
            terms.append(light_keyword(b.light_azimuth.get(), b.light_elevation.get(), b.light_color))
        if b.rim_light_var.get():
            terms.append("rim light")
        return [term for term in terms if term]

    def _style_terms(self) -> list[str]:
        b = self.builder
        terms = [
            *[kw for kw, bv in b.style_toggles.items() if bv.get()],
            *[kw for kw, bv in b.aesthetic_toggles.items() if bv.get()],
            *[kw for kw, bv in b.mood_toggles.items() if bv.get()],
        ]
        motion = b.motion_var.get().strip()
        if motion and motion != "（不指定）":
            terms.append(motion)
        return terms

    def _detail_terms(self) -> list[str]:
        b = self.builder
        return [
            *[kw for kw, bv in b.quality_toggles.items() if bv.get()],
            *[kw for kw, bv in b.texture_toggles.items() if bv.get()],
            *[kw for kw, bv in b.color_toggles.items() if bv.get()],
        ]

    def _active_filter_terms(self) -> list[str]:
        return [kw for kw, bv in self.builder.filter_toggles.items() if bv.get()]

    def _param_zh_lines(self) -> list[str]:
        b = self.builder
        lines = []
        params = PARAMS_ANIME if b.is_anime.get() else PARAMS_REAL
        for name, (_, kw_fn) in params.items():
            if not b.param_checks.get(name, tk.BooleanVar(value=False)).get():
                continue
            custom_val = b.custom_vars.get(name, tk.StringVar()).get().strip()
            kw = custom_val if custom_val and custom_val != "自定义..." else kw_fn(b.param_vars.get(name, tk.StringVar()).get())
            if kw:
                lines.append(f"【{ZH_PARAM_NAMES.get(name, name)}】{kw_to_zh(kw)}")
        return lines

    def _camera_zh_lines(self) -> list[str]:
        b = self.builder
        lines = []
        if b.shot_enabled.get():
            _, desc = SHOT_SCALE[b.shot_var.get()]
            lines.append(f"【景别】{desc.split('—')[0].strip()}")
        if b.elevation_enabled.get():
            _, desc = CAMERA_ELEVATION[b.elevation_var.get()]
            lines.append(f"【俯仰角】{desc.split('—')[0].strip()}")
        if b.subject_angle_enabled.get():
            _, desc = SUBJECT_ANGLE[b.subject_angle_var.get()]
            lines.append(f"【方位角】{desc.split('—')[0].strip()}")
        if b.light_dir_enabled.get():
            lines.append(f"【主光源】{kw_to_zh(light_keyword(b.light_azimuth.get(), b.light_elevation.get(), b.light_color))}")
        if b.rim_light_var.get():
            lines.append("【轮廓光】已启用")
        return lines

    @staticmethod
    def _text_value(widget, hint: str) -> str:
        if widget is None:
            return ""
        value = widget.get("1.0", tk.END).strip()
        return "" if not value or value == hint else value
