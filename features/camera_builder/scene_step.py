import tkinter as tk

from shared.ui_kit import BG_BASE


def create_scene_step(notebook, builder):
    step = tk.Frame(notebook, bg=BG_BASE)
    notebook.add(step, text="1 场景")
    builder.tab_subject = tk.Frame(step, bg=BG_BASE)
    builder.tab_subject.pack(fill=tk.BOTH, expand=True)
    return step
