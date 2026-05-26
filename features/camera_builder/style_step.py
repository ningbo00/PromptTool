import tkinter as tk
from tkinter import ttk

from shared.ui_kit import BG_BASE


def create_style_step(notebook, builder):
    step = tk.Frame(notebook, bg=BG_BASE)
    notebook.add(step, text="2 风格")
    inner = ttk.Notebook(step, style="Dark.TNotebook")
    inner.pack(fill=tk.BOTH, expand=True)

    builder.tab_preset = tk.Frame(inner, bg=BG_BASE)
    builder.tab_style = tk.Frame(inner, bg=BG_BASE)
    builder.tab_filter = tk.Frame(inner, bg=BG_BASE)
    builder.tab_extractor = tk.Frame(inner, bg=BG_BASE)
    inner.add(builder.tab_preset, text="预设")
    inner.add(builder.tab_style, text="情绪")
    inner.add(builder.tab_filter, text="滤镜")
    inner.add(builder.tab_extractor, text="提炼")
    return step
