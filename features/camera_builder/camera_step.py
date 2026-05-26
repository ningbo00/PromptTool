import tkinter as tk
from tkinter import ttk

from shared.ui_kit import BG_BASE, BG_SURFACE


def create_camera_step(notebook, builder):
    step = tk.Frame(notebook, bg=BG_BASE)
    notebook.add(step, text="3 镜头")
    inner = ttk.Notebook(step, style="Dark.TNotebook")
    inner.pack(fill=tk.BOTH, expand=True)

    builder.tab_params = tk.Frame(inner, bg=BG_BASE)
    builder.tab_camera = tk.Frame(inner, bg=BG_SURFACE)
    inner.add(builder.tab_params, text="基础参数")
    inner.add(builder.tab_camera, text="镜头位置")
    return step
